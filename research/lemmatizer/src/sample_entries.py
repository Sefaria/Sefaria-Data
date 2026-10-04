"""Seeded sampling by dictionary and generator, before observing match outcomes.

One Mongo collection scan builds the entry sampling frame. Within a stratum,
headwords are selected by seeded hash order, then forms and refs likewise.
This is a deliberately stratified engineering sample, not frequency-weighted.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import time
import sys
from functools import lru_cache


def rank(seed, *parts):
    return hashlib.sha256(json.dumps([seed, *parts], ensure_ascii=False).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1]/'configs/review_sample.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--db', default='sefaria')
    parser.add_argument('--exclude-dataset', type=Path, action='append', default=[])
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[4]/'Sefaria-Project')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists')
    from pymongo import MongoClient
    cfg = json.loads(args.config.read_text())
    excluded_entries, excluded_forms, excluded_refs = set(), set(), set()
    def rows(path):
        return [json.loads(line) for line in path.read_text().splitlines()]
    for directory in args.exclude_dataset:
        excluded_entries.update((e['dictionary'], e['headword']) for e in rows(directory/'entries.jsonl'))
        excluded_forms.update(w['word_form_id'].split(':')[-1] for w in rows(directory/'word_forms.jsonl'))
        excluded_refs.update(p['ref'] for p in rows(directory/'passages.jsonl'))
        excluded_refs.update(a['source_ref'] for a in rows(directory/'attempts.jsonl'))
    if args.exclude_dataset:
        sys.path.insert(0, str(args.project))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sefaria.settings')
        import django
        django.setup()
        from sefaria.model import Ref
        from sefaria.system.exceptions import InputError
    @lru_cache(maxsize=None)
    def segments(value):
        try:
            ref = Ref(value)
            if getattr(ref.index_node, 'is_virtual', False):
                return {ref.normal()}
            if ref.is_book_level():
                return None
            result = ref.all_segment_refs()
            return {r.normal() for r in result} if len(result) <= 100 else None
        except (InputError, ValueError, KeyError, IndexError):
            return None
    forbidden_segments = set(excluded_refs)
    for value in excluded_refs:
        forbidden_segments.update(segments(value) or [])
    def eligible_ref(value):
        if not args.exclude_dataset:
            return True
        expanded = segments(value)
        return expanded is not None and value not in excluded_refs and not expanded & forbidden_segments
    seed = cfg['seed']
    strata = {(s['dictionary'], s['generated_by']): s for s in cfg['strata']}
    frame = defaultdict(set)
    start = time.perf_counter()
    with MongoClient(os.environ.get('LEMMATIZER_MONGO_URI','mongodb://localhost:27017'), serverSelectionTimeoutMS=5000) as client:
        db = client[args.db]
        for wf in db.word_form.find({'refs.0': {'$exists': True}}, {'lookups':1, 'generated_by':1}):
            for pointer in wf.get('lookups',[]):
                key = pointer.get('parent_lexicon'), wf.get('generated_by')
                if key in strata and pointer.get('headword'):
                    frame[key].add(pointer['headword'])
        selected, refs_by_form, used = [], defaultdict(set), set()
        for key, stratum in strata.items():
            chosen = 0
            for hw in sorted(frame[key], key=lambda h:rank(seed, 'entry', key, h)):
                if (key[0],hw) in used or (key[0],hw) in excluded_entries:
                    continue
                entries = list(db.lexicon_entry.find({'parent_lexicon':key[0], 'headword':hw}, {'_id':1}))
                if not entries:
                    continue
                forms = list(db.word_form.find({'lookups': {'$elemMatch':{'parent_lexicon':key[0], 'headword':hw}},
                                                'generated_by':key[1], 'refs.0':{'$exists':True}}))
                forms.sort(key=lambda w:rank(seed,'form',str(w['_id'])))
                eligible_forms = []
                for wf in forms:
                    if str(wf['_id']) in excluded_forms or any(
                        (p.get('parent_lexicon', p.get('lexicon')), p.get('headword')) in excluded_entries
                        for p in wf.get('lookups', [])):
                        continue
                    wf['refs'] = [r for r in wf['refs'] if eligible_ref(r)]
                    if wf['refs']:
                        eligible_forms.append(wf)
                    if len(eligible_forms) == cfg['forms_per_entry']:
                        break
                forms = eligible_forms
                if not forms:
                    continue
                for wf in forms:
                    refs = sorted(set(wf['refs']),key=lambda r:rank(seed,'ref',str(wf['_id']),r))[:cfg['refs_per_form']]
                    refs_by_form[str(wf['_id'])].update(refs)
                selected.append({**stratum, 'headword':hw, 'entry_ids':[str(e['_id']) for e in entries],
                                 'sampled_form_ids':[str(w['_id']) for w in forms], 'frame_headwords':len(frame[key])})
                used.add((key[0],hw)); chosen += 1
                if chosen == stratum['entries']:
                    break
            if chosen != stratum['entries']:
                raise ValueError(f'Insufficient frame for {key}: {chosen}')
    plan = {'schema_version':'stratified-entry-sample-v1', 'sampling_config':cfg, 'selected_entries':selected,
            'selectors':[], 'word_form_refs':[{'word_form_id':wid,'refs':sorted(refs)} for wid,refs in sorted(refs_by_form.items())],
            'exclusions': {'datasets':[str(p) for p in args.exclude_dataset], 'entry_headwords':len(excluded_entries), 'word_forms':len(excluded_forms), 'source_and_segment_refs':len(forbidden_segments), 'policy':'Exclude all prior entry headwords and WordForms, any form pointing to a prior entry, and any source ref overlapping prior segments; unexpandable or broad refs excluded when checking independence.'},
            'sampling_seconds':time.perf_counter()-start,
            'note':'Unique headwords per dictionary used as sampling units, not asserted lexeme identities. Entry groups are disjoint across generator strata by config order. No matching outcomes used in selection.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'entries':len(selected),'forms':len(refs_by_form),'attempts':sum(map(len,refs_by_form.values())), 'seconds':plan['sampling_seconds']}))


if __name__ == '__main__':
    main()
