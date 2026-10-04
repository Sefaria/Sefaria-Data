#!/usr/bin/env python3
"""Read-only Sefaria occurrence extraction. Historical WordForm experiment; Backend/Store also support citation extraction.

Outputs candidate associations, not adjudicated lemmas. No Mongo writes.
SQLite staging keeps the work queue and output records off the Python heap.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

from extraction_core import (MATCH_MODES, MATCHING_VERSION, PROCESSING_VERSION, find_spans,
                             plain_text, ranked_hebrew_versions, sha, stable_id)


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


class Store:
    def __init__(self, directory):
        self.db = sqlite3.connect(directory / 'staging.sqlite')
        self.db.executescript('''
        CREATE TABLE records(kind TEXT, id TEXT, data TEXT, PRIMARY KEY(kind,id));
        CREATE TABLE work(ref TEXT, wf TEXT, PRIMARY KEY(ref,wf));
        CREATE TABLE associations(occurrence TEXT, id TEXT, data TEXT, PRIMARY KEY(occurrence,id));
        ''')

    def put(self, kind, key, data):
        self.db.execute('INSERT OR REPLACE INTO records VALUES (?,?,?)', (kind, key, dumps(data)))

    def get(self, kind, key):
        row = self.db.execute('SELECT data FROM records WHERE kind=? AND id=?', (kind, key)).fetchone()
        return json.loads(row[0]) if row else None

    def export(self, directory):
        for kind in ('entries', 'word_forms', 'passages', 'occurrences', 'attempts', 'version_selections'):
            with (directory / (kind + '.jsonl')).open('w', encoding='utf-8') as out:
                for key, raw in self.db.execute('SELECT id,data FROM records WHERE kind=? ORDER BY id', (kind,)):
                    record = json.loads(raw)
                    if kind == 'occurrences':
                        record['associations'] = [json.loads(r[0]) for r in self.db.execute(
                            'SELECT data FROM associations WHERE occurrence=? ORDER BY id', (key,))]
                    out.write(dumps(record) + '\n')


class Backend:
    def __init__(self, project, store):
        sys.path.insert(0, str(project))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sefaria.settings')
        import django
        django.setup()
        from sefaria.model import Ref, Version, TextChunk
        from sefaria.system.database import db
        from sefaria.system.exceptions import InputError
        self.Ref, self.Version, self.TextChunk, self.db = Ref, Version, TextChunk, db
        self.InputError = InputError
        self.store = store

    @lru_cache(maxsize=4)
    def versions(self, title):
        versions = ranked_hebrew_versions(list(self.db.texts.find({'title': title})))
        def meta(v):
            return {k: v.get(k) for k in ('_id', 'versionTitle', 'language', 'actualLanguage',
                    'languageFamilyName', 'isPrimary', 'priority', 'license', 'versionSource')}
        self.store.put('version_selections', title, {
            'work': title, 'policy': 'primary-hebrew-priority-v1',
            'ordered_versions': [meta(v) for v in versions],
            'no_primary_flag': bool(versions) and not any(v.get('isPrimary') for v in versions),
        })
        return versions

    @lru_cache(maxsize=4096)
    def passage(self, segment_ref):
        ref = self.Ref(segment_ref)
        versions = self.versions(ref.index.title)
        skipped = []
        for rank, version in enumerate(versions):
            obj = self.Version(version)
            try:
                raw = obj.sub_content_with_ref(ref)
            except (IndexError, KeyError):
                skipped.append({'version_id': str(version['_id']), 'reason': 'missing_segment_or_node'})
                continue
            if not isinstance(raw, str):
                raise ValueError('Expected segment string: ' + segment_ref)
            text = plain_text(raw)
            if not text:
                skipped.append({'version_id': str(version['_id']), 'reason': 'empty_text'})
                continue
            pid = stable_id('passage', str(version['_id']), segment_ref, sha(text), PROCESSING_VERSION)
            result = {'passage_id': pid, 'ref': segment_ref, 'work': ref.index.title,
                      'version_id': str(version['_id']), 'version_title': version['versionTitle'],
                      'version_language': version.get('language'),
                      'actual_language': version.get('actualLanguage'),
                      'language_family': version.get('languageFamilyName'),
                      'version_priority': version.get('priority', 0),
                      'version_is_primary': version.get('isPrimary', False),
                      'version_selection_rank': rank, 'is_fallback': rank > 0, 'skipped_versions': skipped,
                      'license': version.get('license'), 'raw_text': raw, 'text': text,
                      'raw_text_sha256': sha(raw), 'text_sha256': sha(text),
                      'text_processing_version': PROCESSING_VERSION}
            self.store.put('passages', pid, result)
            return result
        return None

    @lru_cache(maxsize=10000)
    def resolve_lookup(self, encoded):
        lookup = json.loads(encoded)
        query = {k: v for k, v in lookup.items() if k not in ('primary', 'lexicon')}
        if 'parent_lexicon' not in query and lookup.get('lexicon'):
            query['parent_lexicon'] = lookup['lexicon']
        if not query.get('parent_lexicon') or not query.get('headword'):
            return []
        ids = []
        for entry in self.db.lexicon_entry.find(query).sort('_id', 1):
            eid = 'entry:' + str(entry['_id'])
            self.store.put('entries', eid, {'entry_id': eid, 'source_entry_id': str(entry['_id']),
                'dictionary': entry['parent_lexicon'], 'headword': entry['headword'],
                'source_identifiers': {k: entry[k] for k in ('rid', 'strong_number', 'strong_numbers') if k in entry},
                'entry_snapshot': entry})
            ids.append(eid)
        return ids


def collect(backend, store, config, max_forms, max_refs, all_word_forms=False):
    selected = []
    counts = Counter()
    queries = []
    explicit = {r['word_form_id']: r['refs'] for r in config.get('word_form_refs', [])}
    if explicit:
        from bson import ObjectId
        queries.append({'_id': {'$in': [ObjectId(wid) for wid in explicit]}})
    if all_word_forms:
        queries.append({'refs.0': {'$exists': True}})
    for selector in ([] if all_word_forms else config.get('selectors', [])):
        lexicon = selector['dictionary']
        if 'headword' in selector:
            heads = [selector['headword']]
        else:
            seed = backend.db.word_form.find_one({'c_form': selector['seed_c_form'],
                'lookups.parent_lexicon': lexicon, 'refs.0': {'$exists': True}}, sort=[('_id', 1)])
            if not seed:
                raise ValueError('No seed for ' + dumps(selector))
            heads = sorted({p['headword'] for p in seed['lookups'] if p.get('parent_lexicon') == lexicon})
        for headword in heads:
            selected.append({'dictionary': lexicon, 'headword': headword})
            queries.append({'lookups': {'$elemMatch': {'parent_lexicon': lexicon, 'headword': headword}},
                            'refs.0': {'$exists': True}})
    for query in queries:
        cursor = backend.db.word_form.find(query).sort('_id', 1)
        if max_forms and not explicit:
            cursor = cursor.limit(max_forms)
        for wf in cursor:
            wid = str(wf['_id'])
            if store.get('word_forms', wid):
                continue
            links = []
            for lookup in wf.get('lookups', []):
                ids = backend.resolve_lookup(dumps(lookup))
                links.append({'lookup': lookup, 'entry_ids': ids})
                counts['unresolved_lookup_pointers'] += not bool(ids)
            refs = sorted(set(wf.get('refs', [])))
            sampled_refs = explicit[wid] if explicit else (refs[:max_refs] if max_refs else refs)
            if not set(sampled_refs) <= set(refs):
                raise ValueError('Sample references are no longer on WordForm ' + wid)
            store.put('word_forms', wid, {'word_form_id': wid, 'source_record': wf,
                'resolved_lookups': links, 'total_distinct_refs': len(refs),
                'selected_refs': sampled_refs})
            counts['selected_word_forms'] += 1
            counts['available_distinct_ref_items'] += len(refs)
            for ref in sampled_refs:
                store.db.execute('INSERT OR IGNORE INTO work VALUES (?,?)', (ref, wid))
                counts['selected_ref_items'] += 1
    store.db.commit()
    return config.get('selected_entries', selected), dict(counts)


def extract(backend, store, max_segments, modes):
    counts = Counter()
    # Ref grouping makes overlapping dictionary evidence reuse text retrieval.
    for (source_ref,) in store.db.execute('SELECT DISTINCT ref FROM work ORDER BY ref'):
        passages, issue, error_details = [], None, None
        try:
            ref = backend.Ref(source_ref)
            if getattr(ref.index_node, 'is_virtual', False):
                issue = 'dictionary_or_virtual_ref'
            elif ref.is_book_level():
                issue = 'ref_too_broad'
            else:
                segments = ref.all_segment_refs()
                if not segments:
                    issue = 'no_segments'
                elif len(segments) > max_segments:
                    issue = 'ref_too_broad'
                else:
                    for segment in segments:
                        p = backend.passage(segment.normal())
                        if p:
                            passages.append(p)
                    if not passages:
                        issue = 'missing_hebrew_text'
        except (backend.InputError, ValueError, KeyError, IndexError) as exc:
            issue = 'ref_or_text_error:' + type(exc).__name__
            error_details = str(exc)
        counts['source_refs'] += 1
        for (wid,) in store.db.execute('SELECT wf FROM work WHERE ref=? ORDER BY wf', (source_ref,)):
            record = store.get('word_forms', wid)
            wf = record['source_record']
            matches, method = [], None
            if not issue:
                for mode in modes:
                    matches = [(p, a, b) for p in passages for a, b in find_spans(p['text'], wf['form'], mode)]
                    if matches:
                        method = mode
                        break
            ids = []
            for p, a, b in matches:
                oid = stable_id('occurrence', p['passage_id'], a, b)
                ids.append(oid)
                store.put('occurrences', oid, {'occurrence_id': oid, 'passage_id': p['passage_id'],
                    'start_char': a, 'end_char': b, 'surface': p['text'][a:b],
                    'left_context': p['text'][max(0, a-50):a], 'right_context': p['text'][b:b+50],
                    'review_status': 'unreviewed'})
                for link in record['resolved_lookups']:
                    for eid in link['entry_ids']:
                        aid = stable_id('association', wid, source_ref, eid, oid, link['lookup'])
                        association = {'entry_id': eid, 'word_form_id': wid, 'word_form': wf['form'],
                            'lookup': link['lookup'], 'lookup_resolution_count': len(link['entry_ids']),
                            'source_ref': source_ref, 'generated_by': wf.get('generated_by'),
                            'match_method': method, 'matches_in_source_ref': len(matches),
                            'review_status': 'unreviewed'}
                        store.db.execute('INSERT OR IGNORE INTO associations VALUES (?,?,?)', (oid, aid, dumps(association)))
            status = issue or ('matched_unique' if len(matches) == 1 else 'matched_multiple' if matches else 'no_match')
            counts[status] += 1
            if method:
                counts['method:' + method] += 1
            store.put('attempts', stable_id('attempt', wid, source_ref), {
                'word_form_id': wid, 'source_ref': source_ref, 'status': status, 'error_details': error_details,
                'match_method': method, 'candidate_occurrence_ids': ids,
                'searched_passage_ids': [p['passage_id'] for p in passages],
                'partial_text_coverage': bool(passages) and len(passages) < len(segments),
                'unresolved_lookups': [l['lookup'] for l in record['resolved_lookups'] if not l['entry_ids']]})
        if counts['source_refs'] % 50 == 0:
            store.db.commit()
            print('Processed source refs:', counts['source_refs'], flush=True)
    store.db.commit()
    return dict(counts)


def revision(path):
    return subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[4] / 'Sefaria-Project')
    parser.add_argument('--all-word-forms', action='store_true', help='Full ref-bearing collection; ignores seed config; requires both sampling limits set to 0')
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1] / 'configs' / 'pilot.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-forms-per-entry', type=int, default=12, help='0 means unlimited')
    parser.add_argument('--max-refs-per-form', type=int, default=4, help='0 means unlimited')
    parser.add_argument('--max-segments-per-ref', type=int, default=100)
    parser.add_argument('--verify-native-texts', type=int, default=20, help='Compare cached extraction with independent TextChunk reads; 0 disables')
    parser.add_argument('--match-modes', default=','.join(MATCH_MODES))
    args = parser.parse_args()
    if args.max_forms_per_entry < 0 or args.max_refs_per_form < 0 or args.max_segments_per_ref < 1 or args.verify_native_texts < 0:
        parser.error('Invalid limits')
    if args.all_word_forms and (args.max_forms_per_entry or args.max_refs_per_form):
        parser.error('--all-word-forms requires --max-forms-per-entry 0 --max-refs-per-form 0')
    modes = args.match_modes.split(',')
    if not modes or any(m not in MATCH_MODES for m in modes):
        parser.error('Invalid match modes')
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    store = Store(args.output)
    manifest = {'schema_version': 'occurrence-candidates-v1', 'started_at': datetime.now(timezone.utc).isoformat(),
                'status': 'running', 'parameters': vars(args), 'matching_version': MATCHING_VERSION,
                'processing_version': PROCESSING_VERSION,
                'data_repo_commit': revision(Path(__file__).resolve().parents[3]),
                'project_commit': revision(args.project),
                'snapshot_note': 'Live local DB read; not a transactionally frozen backup.',
                'script_sha256': sha(Path(__file__).read_text()),
                'core_sha256': sha(Path(__file__).with_name('extraction_core.py').read_text())}
    (args.output / 'manifest.json').write_text(dumps(manifest) + '\n')
    backend = Backend(args.project, store)
    manifest['database'] = backend.db.name
    initialized = time.perf_counter()
    config = {'selectors': [], 'description': 'Full ref-bearing WordForm collection'} if args.all_word_forms else json.loads(args.config.read_text())
    manifest['config'] = config
    selected, selection_counts = collect(backend, store, config, args.max_forms_per_entry, args.max_refs_per_form, args.all_word_forms)
    collected = time.perf_counter()
    stats = extract(backend, store, args.max_segments_per_ref, modes)
    extracted = time.perf_counter()
    verified = 0
    for (raw,) in store.db.execute("SELECT data FROM records WHERE kind='passages' ORDER BY id LIMIT ?", (args.verify_native_texts,)):
        p = json.loads(raw)
        reference_text = backend.TextChunk(backend.Ref(p['ref']), lang=p['version_language'], vtitle=p['version_title'], fallback_on_default_version=False).text
        if reference_text != p['raw_text']:
            raise AssertionError('Native text verification failed: ' + p['ref'])
        verified += 1
    missing_verified = 0
    if args.verify_native_texts:
        for (source_ref,) in store.db.execute("SELECT DISTINCT json_extract(data, '$.source_ref') FROM records WHERE kind='attempts' AND json_extract(data, '$.status')='missing_hebrew_text' ORDER BY 1"):
            ref = backend.Ref(source_ref)
            if not ref.is_segment_level() or backend.passage(ref.normal()) is not None:
                continue
            for v in backend.versions(ref.index.title):
                reference_text = backend.TextChunk(ref, lang=v['language'], vtitle=v['versionTitle'], fallback_on_default_version=False).text
                if isinstance(reference_text, str) and plain_text(reference_text):
                    raise AssertionError('Missing-text verification failed: ' + source_ref)
            missing_verified += 1
            if missing_verified >= args.verify_native_texts:
                break
    manifest['native_missing_refs_verified'] = missing_verified
    manifest['native_texts_verified'] = verified
    store.export(args.output)
    sizes = dict(store.db.execute('SELECT kind, COUNT(*) FROM records GROUP BY kind'))
    manifest.update(status='complete', selected_entries=selected, selection_counts=selection_counts,
                    extraction_counts=stats, output_counts=sizes,
                    timings_seconds={'initialize': initialized-started, 'collect': collected-initialized,
                                     'extract': extracted-collected, 'total': time.perf_counter()-started})
    (args.output / 'manifest.json').write_text(dumps(manifest) + '\n')
    store.db.close()
    print(dumps({k: manifest[k] for k in ('selected_entries', 'selection_counts', 'extraction_counts', 'output_counts', 'timings_seconds')}))


if __name__ == '__main__':
    main()
