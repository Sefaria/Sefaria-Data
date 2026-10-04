"""Seeded, read-only dictionary-link yield measurement; no WordForms or LLMs."""
import argparse
from collections import Counter, defaultdict
from html import unescape
import hashlib
import json
from pathlib import Path
import time

from audit_dictionary_links import TITLES, title
from build_dataset import Backend, Store
from build_citation_dataset import ANCHOR, VERSION, definitions, extract
from extraction_core import plain_text, sha


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--per-dictionary', type=int, default=250)
    parser.add_argument('--seed', default='20261004-citation-yield-v1')
    parser.add_argument('--max-segments', type=int, default=100)
    parser.add_argument('--exclude', type=Path, help='Optional prior cases JSONL whose link IDs should be excluded')
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[4]/'Sefaria-Project')
    args = parser.parse_args()
    if args.per_dictionary < 1 or args.max_segments < 1:
        parser.error('Limits must be positive')
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    store = Store(args.output)
    backend = Backend(args.project, store)
    excluded = ({str(c['link']['_id']) for c in map(json.loads, args.exclude.read_text().splitlines())}
                if args.exclude else set())
    frames = defaultdict(list)
    for link in backend.db.links.find({'refs': {'$regex': r'^(Jastrow|Klein Dictionary|BDB)(,| |$)'}}):
        refs = link.get('refs', [])
        dictionaries = [r for r in refs if title(r)]
        if len(refs) == 2 and len(dictionaries) == 1 and str(link['_id']) not in excluded:
            frames[title(dictionaries[0])].append(link)
    selected = []
    for dictionary in TITLES:
        ordered = sorted(frames[dictionary], key=lambda l: sha(args.seed+':'+str(l['_id'])))
        selected.extend((dictionary, link) for link in ordered[:args.per_dictionary])
    manifest = {'status': 'running', 'seed': args.seed, 'rule_version': VERSION,
        'sampling': 'Smallest seeded link hashes, equal quota per dictionary, prior audit link IDs excluded. Entries may repeat. This is link sampling, not uniform lemma sampling.',
        'per_dictionary': args.per_dictionary, 'max_segments': args.max_segments,
        'excluded_links': len(excluded), 'frame_links': {TITLES[k]: len(v) for k,v in frames.items()},
        'selected': len(selected), 'wordforms_used': False, 'llm_used': False,
        'source_database_writes': False, 'version_policy': 'primary-hebrew-priority-v1; fallback only for missing/empty segments'}
    dump(args.output/'manifest.json', manifest)
    snapshots = args.output/'source'
    snapshots.mkdir()
    for name in ['measure_citation_yield.py', 'build_citation_dataset.py', 'build_dataset.py', 'extraction_core.py', 'audit_dictionary_links.py']:
        (snapshots/name).write_bytes(Path(__file__).with_name(name).read_bytes())
    attempts, examples = [], {}
    with (args.output/'cases.jsonl').open('w') as case_file, (args.output/'attempts.jsonl').open('w') as attempt_file:
        for number, (dictionary, link) in enumerate(selected, 1):
            dictionary_ref = next(r for r in link['refs'] if title(r) == dictionary)
            target = next(r for r in link['refs'] if r != dictionary_ref)
            case = {'audit_id': f'Y{number:04d}', 'dictionary': TITLES[dictionary],
                'dictionary_ref': dictionary_ref, 'target_ref': target, 'link': link, 'passages': []}
            try:
                entry = backend.Ref(dictionary_ref).index_node.lexicon_entry
                case['entry'] = entry.contents()
                case['entry_html'] = entry.as_strings()
                ref = backend.Ref(target)
                case['categories'] = ref.index.categories
                if getattr(ref.index_node, 'is_virtual', False) or ref.is_book_level():
                    raise ValueError('virtual or book-level target')
                segments = ref.all_segment_refs()
                case['target_segment_count'] = len(segments)
                if len(segments) > args.max_segments:
                    raise ValueError('target exceeds segment cap')
                for segment in segments:
                    passage = backend.passage(segment.normal())
                    if passage:
                        case['passages'].append(passage)
                    else:
                        case.setdefault('missing_segments', []).append(segment.normal())
                if case.get('missing_segments'):
                    raise ValueError('incomplete primary Hebrew target text')
            except (ValueError, KeyError, AttributeError, IndexError, backend.InputError) as error:
                case['error'] = str(error)
            example, reason = extract(case)
            anchor_count = sum(unescape(a[1]) == target
                for _, html in definitions(case.get('entry', {}).get('content', {}))
                for a in ANCHOR.finditer(html))
            attempt = {'audit_id': case['audit_id'], 'dictionary': case['dictionary'],
                'dictionary_ref': dictionary_ref, 'target_ref': target,
                'categories': case.get('categories', []), 'link_id': str(link['_id']),
                'status': 'accepted' if example else 'skipped', 'reason': reason,
                'source_error': case.get('error'), 'exact_citation_anchor_count': anchor_count,
                'example_id': example['example_id'] if example else None}
            if example:
                examples[example['example_id']] = example
            attempts.append(attempt)
            case_file.write(json.dumps(case, ensure_ascii=False, default=str)+'\n')
            attempt_file.write(json.dumps(attempt, ensure_ascii=False)+'\n')
            case_file.flush(); attempt_file.flush()
            if number % 100 == 0:
                print(json.dumps({'processed': number, 'accepted_links': sum(a['status']=='accepted' for a in attempts), 'unique_examples': len(examples), 'seconds': round(time.monotonic()-started,1)}), flush=True)
    with (args.output/'examples.jsonl').open('w') as handle:
        for example in examples.values():
            handle.write(json.dumps(example, ensure_ascii=False, default=str)+'\n')
    store.db.commit()
    with (args.output/'version_selections.jsonl').open('w') as handle:
        for (data,) in store.db.execute("SELECT data FROM records WHERE kind='version_selections' ORDER BY id"):
            handle.write(data+'\n')
    groups = {}
    for dictionary in TITLES.values():
        aa = [a for a in attempts if a['dictionary']==dictionary]
        ee = [e for e in examples.values() if e['dictionary']==dictionary]
        groups[dictionary] = {'attempts': len(aa), 'accepted_links': sum(a['status']=='accepted' for a in aa),
            'unique_examples': len(ee), 'distinct_entry_keys': len({e['entry_key'] for e in ee}),
            'rejections': dict(Counter(a['reason'] for a in aa if a['reason'])),
            'no_exact_citation_anchor': sum(a['exact_citation_anchor_count']==0 for a in aa)}
    categories = {}
    for category in sorted({(a['categories'] or ['Unknown'])[0] for a in attempts}):
        aa = [a for a in attempts if (a['categories'] or ['Unknown'])[0]==category]
        categories[category] = {'attempts': len(aa), 'accepted_links': sum(a['status']=='accepted' for a in aa)}
    manifest.update(status='complete', elapsed_seconds=round(time.monotonic()-started,2),
        accepted_links=sum(a['status']=='accepted' for a in attempts), unique_examples=len(examples),
        distinct_entry_keys=len({e['entry_key'] for e in examples.values()}), dictionaries=groups,
        categories=categories, rejection_reasons=dict(Counter(a['reason'] for a in attempts if a['reason'])))
    dump(args.output/'manifest.json', manifest)
    lines = ['# Conservative dictionary-link yield measurement', '',
        f"{len(attempts)} sampled links; {manifest['accepted_links']} accepted links; {len(examples)} unique examples; {manifest['distinct_entry_keys']} dictionary-specific lemmas.", '',
        '| Dictionary | Sampled | Accepted links | Unique examples | Lemmas |', '|---|---:|---:|---:|---:|']
    for d,g in groups.items():
        lines.append(f"| {d} | {g['attempts']} | {g['accepted_links']} | {g['unique_examples']} | {g['distinct_entry_keys']} |")
    lines += ['', '## Rejections', '', json.dumps(manifest['rejection_reasons'], indent=2), '',
        '## Corpus categories', '', json.dumps(categories, ensure_ascii=False, indent=2), '',
        'Equal dictionary quotas are not the natural library mixture. Overall percentage is sample yield, not a corpus-wide recall estimate. Supported evidence rules differ by dictionary. Zero exact anchors can reflect ref-normalization/HTML coverage defects, not missing lexical evidence. Accepted examples are deterministic proposals, not expert-verified gold.', '',
        f"Elapsed: {manifest['elapsed_seconds']} seconds. Full snapshots, original offsets, frozen text hashes and version metadata are retained."]
    (args.output/'REPORT.md').write_text('\n'.join(lines)+'\n')
    store.db.close()
    print(json.dumps(manifest, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
