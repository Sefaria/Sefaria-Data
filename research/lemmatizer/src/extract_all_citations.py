"""Resumable full dictionary-link extraction with conservative citation rules and tqdm."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import sqlite3
import time

from tqdm import tqdm
from audit_dictionary_links import TITLES, title
from build_dataset import Backend, Store, dumps
from build_citation_dataset import VERSION, evidence, extract

QUERY = {'refs': {'$regex': r'^(Jastrow|Klein Dictionary|BDB)(,| |$)'}}
SOURCES = ('extract_all_citations.py', 'build_citation_dataset.py', 'build_dataset.py',
           'extraction_core.py', 'audit_dictionary_links.py')


class RunStore(Store):
    def __init__(self, directory):
        self.db = sqlite3.connect(directory / 'staging.sqlite')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS records(kind TEXT, id TEXT, data TEXT,
                PRIMARY KEY(kind,id));
            CREATE TABLE IF NOT EXISTS queue(id TEXT PRIMARY KEY, data TEXT, done INTEGER DEFAULT 0);
            CREATE INDEX IF NOT EXISTS queue_pending ON queue(done,id);
            CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, data TEXT);
            CREATE TABLE IF NOT EXISTS examples(id TEXT PRIMARY KEY, entry_key TEXT, data TEXT);
            CREATE INDEX IF NOT EXISTS examples_entry ON examples(entry_key);
            CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT);
        ''')

    def meta(self, key):
        row = self.db.execute('SELECT value FROM metadata WHERE key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def set_meta(self, key, value):
        self.db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)', (key, dumps(value)))


def build_case(backend, link, max_segments):
    refs = link['refs']
    dr = next(r for r in refs if title(r))
    target = next(r for r in refs if r != dr)
    case = {'audit_id': 'L' + str(link['_id']), 'dictionary': TITLES[title(dr)],
            'dictionary_ref': dr, 'target_ref': target, 'link': link, 'passages': []}
    try:
        case['entry'] = backend.Ref(dr).index_node.lexicon_entry.contents()
        # No target text is needed when no rule can propose a form. This changes
        # rejection accounting, but not the set of accepted examples.
        if not next(evidence(case), None):
            return case, None, 'no_supported_evidence_rule'
        ref = backend.Ref(target)
        case['categories'] = ref.index.categories
        if getattr(ref.index_node, 'is_virtual', False) or ref.is_book_level():
            raise ValueError('virtual or book-level target')
        segments = ref.all_segment_refs()
        if len(segments) > max_segments:
            raise ValueError('target exceeds segment cap')
        for segment in segments:
            passage = backend.passage(segment.normal())
            if not passage:
                raise ValueError('incomplete primary Hebrew target text')
            case['passages'].append(passage)
    except (ValueError, KeyError, AttributeError, IndexError, backend.InputError) as error:
        case['error'] = str(error)
    example, reason = extract(case)
    return case, example, reason


def record_result(store, link, case, example, reason):
    attempt = {k: case[k] for k in ('audit_id', 'dictionary', 'dictionary_ref', 'target_ref')}
    attempt.update(link_id=str(link['_id']), status='accepted' if example else 'skipped',
                   reason=reason, source_error=case.get('error'),
                   example_id=example['example_id'] if example else None)
    store.db.execute('INSERT INTO attempts VALUES (?,?)', (str(link['_id']), dumps(attempt)))
    store.db.execute('UPDATE queue SET done=1 WHERE id=?', (str(link['_id']),))
    if example:
        store.db.execute('INSERT OR IGNORE INTO examples VALUES (?,?,?)',
                         (example['example_id'], example['entry_key'], dumps(example)))
        store.put('accepted_cases', str(link['_id']), case)


def export_run(store, output, status):
    counts = Counter()
    by_dictionary = {}
    for (raw,) in store.db.execute('SELECT data FROM attempts'):
        a = json.loads(raw)
        counts[a['reason'] or 'accepted_links'] += 1
        group = by_dictionary.setdefault(a['dictionary'], Counter())
        group[a['reason'] or 'accepted_links'] += 1
    queries = {
        'examples': 'SELECT data FROM examples ORDER BY id',
        'attempts': 'SELECT data FROM attempts ORDER BY id',
        'cases': "SELECT data FROM records WHERE kind='accepted_cases' ORDER BY id",
        'version_selections': "SELECT data FROM records WHERE kind='version_selections' ORDER BY id",
    }
    for name, query in tqdm(queries.items(), desc='Export files', unit='file'):
        tmp = output / (name + '.jsonl.tmp')
        with tmp.open('w', encoding='utf-8') as handle:
            for (raw,) in store.db.execute(query):
                handle.write(raw + '\n')
        tmp.replace(output / (name + '.jsonl'))
    distribution = Counter()
    tmp = output / 'lemmas.jsonl.tmp'
    with tmp.open('w', encoding='utf-8') as handle:
        for key, n in store.db.execute('SELECT entry_key,COUNT(*) FROM examples GROUP BY entry_key'):
            examples = [json.loads(row[0]) for row in store.db.execute(
                'SELECT data FROM examples WHERE entry_key=? ORDER BY id', (key,))]
            first = examples[0]
            row = {'entry_key': key, 'dictionary': first['dictionary'], 'headword': first['headword'],
                   'occurrence_count': n, 'example_ids': [e['example_id'] for e in examples],
                   'distinct_surfaces': sorted({e['surface'] for e in examples}),
                   'dictionary_refs': sorted({e['dictionary_ref'] for e in examples})}
            handle.write(dumps(row) + '\n')
            distribution[n] += 1
    tmp.replace(output / 'lemmas.jsonl')
    report = {'status': status, 'rule_version': VERSION,
              'candidate_links': store.db.execute('SELECT COUNT(*) FROM queue').fetchone()[0],
              'processed_links': sum(counts.values()), 'outcomes': dict(counts),
              'dictionaries': by_dictionary,
              'unique_examples': store.db.execute('SELECT COUNT(*) FROM examples').fetchone()[0],
              'distinct_entries': sum(distribution.values()),
              'occurrences_per_entry_distribution': dict(distribution),
              'entries_with_2plus': sum(n for size, n in distribution.items() if size >= 2),
              'entries_with_3plus': sum(n for size, n in distribution.items() if size >= 3),
              'configuration': store.meta('configuration'),
              'inventory': store.meta('inventory'),
              'expert_verified': False, 'source_database_writes': False}
    tmp = output / 'report.json.tmp'
    tmp.write_text(dumps(report) + '\n', encoding='utf-8')
    tmp.replace(output / 'report.json')
    print(json.dumps({k: report[k] for k in ('status', 'processed_links', 'unique_examples',
                                           'distinct_entries', 'entries_with_2plus', 'entries_with_3plus')}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[4]/'Sefaria-Project')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--max-segments', type=int, default=100)
    parser.add_argument('--limit', type=int, help='Process at most this many pending links (smoke test only)')
    args = parser.parse_args()
    if args.max_segments < 1 or (args.limit is not None and args.limit < 1):
        parser.error('Limits must be positive')
    if args.resume:
        if not (args.output / 'staging.sqlite').exists():
            parser.error('--resume needs an existing run with staging.sqlite')
    else:
        args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / '.run.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error('Another process is using this output directory')
        store = RunStore(args.output)
        source_bytes = {name: Path(__file__).with_name(name).read_bytes() for name in SOURCES}
        config = {'max_segments': args.max_segments, 'project': str(args.project.resolve()),
                  'rule_version': VERSION, 'source_sha256': {
                      name: hashlib.sha256(data).hexdigest() for name, data in source_bytes.items()}}
        previous = store.meta('configuration')
        if previous and previous != config:
            parser.error('Source code or configuration changed; use a new output directory')
        store.set_meta('configuration', config)
        (args.output / 'source').mkdir(exist_ok=True)
        for name, data in source_bytes.items():
            (args.output / 'source' / name).write_bytes(data)
        store.db.commit()
        try:
            print('Loading Sefaria and connecting to the local database...', flush=True)
            backend = Backend(args.project, store)
            if not store.meta('inventory'):
                # An interrupted inventory is rebuilt before any extraction starts.
                store.db.execute('DELETE FROM queue')
                total = backend.db.links.count_documents(QUERY)
                candidates = 0
                with backend.db.links.find(QUERY).batch_size(500) as cursor:
                    for i, link in enumerate(tqdm(cursor, total=total, desc='Inventory links', unit='link'), 1):
                        refs = link.get('refs', [])
                        if len(refs) == 2 and sum(bool(title(r)) for r in refs) == 1:
                            store.db.execute('INSERT INTO queue(id,data) VALUES (?,?)', (str(link['_id']), dumps(link)))
                            candidates += 1
                        if i % 1000 == 0:
                            store.db.commit()
                store.set_meta('inventory', {'candidate_links': candidates,
                    'completed_at': datetime.now(timezone.utc).isoformat(),
                    'scope': 'All BDB, BDB Aramaic, Jastrow and Klein dictionary-to-corpus links; no sampling'})
                store.db.commit()
            total = store.db.execute('SELECT COUNT(*) FROM queue').fetchone()[0]
            done = store.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0]
            skipped = store.db.execute(
                "SELECT COUNT(*) FROM attempts WHERE json_extract(data,'$.status')='skipped'").fetchone()[0]
            processed = 0
            started = time.monotonic()
            with tqdm(total=total, initial=done, desc='Extract occurrences', unit='link') as bar:
                while args.limit is None or processed < args.limit:
                    size = min(100, args.limit - processed) if args.limit else 100
                    batch = store.db.execute('''SELECT q.data FROM queue q
                        WHERE q.done=0
                        ORDER BY q.id LIMIT ?''', (size,)).fetchall()
                    if not batch:
                        break
                    for (raw,) in batch:
                        link = json.loads(raw)
                        case, example, reason = build_case(backend, link, args.max_segments)
                        record_result(store, link, case, example, reason)
                        skipped += int(example is None)
                        processed += 1
                        bar.update()
                    store.db.commit()
                    accepted = store.db.execute('SELECT COUNT(*) FROM examples').fetchone()[0]
                    bar.set_postfix(examples=accepted, skipped=skipped)
            remaining = total - done - processed
            export_run(store, args.output, 'paused' if remaining else 'complete')
            print(f'Extraction this invocation: {time.monotonic() - started:.1f}s. Output: {args.output.resolve()}')
        except KeyboardInterrupt:
            store.db.rollback()
            print('\nInterrupted. Committed batches are safe; rerun with --resume. JSONL exports may be incomplete.', flush=True)
            raise SystemExit(130)
        finally:
            store.db.close()


if __name__ == '__main__':
    main()
