"""Prepare model inputs separately from dictionary-derived reference labels. No models loaded."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from benchmark_core import POLICY, map_target


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--cases', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--policy', choices=[POLICY, 'raw-v1'], default=POLICY)
    args = parser.parse_args()
    categories = {}
    with (args.cases or args.input.with_name('cases.jsonl')).open() as source:
        for line in source:
            case = json.loads(line)
            for p in case.get('passages', []):
                if case.get('categories'):
                    old = categories.setdefault(p['ref'], case['categories'])
                    if old != case['categories']:
                        raise ValueError('Conflicting categories')
    args.output.mkdir(parents=True, exist_ok=False)
    passages, targets, seen = {}, {}, set()
    assignments = defaultdict(set)
    counts, dictionary_counts, category_counts = Counter(), Counter(), Counter()
    with args.input.open() as source, (args.output/'labels.jsonl').open('w') as labels:
        for line in source:
            e = json.loads(line)
            if e['example_id'] in seen:
                raise ValueError('Duplicate example ID')
            seen.add(e['example_id'])
            if sha(e['text']) != e['text_sha256']:
                raise ValueError('Source hash mismatch')
            text, a, b, boundaries = map_target(e['text'], e['start_char'], e['end_char'],
                                                e['surface'], args.policy)
            pid = e['passage_id']
            record = {'passage_id': pid, 'original_text': e['text'], 'text': text,
                      'text_sha256': sha(text), 'original_text_sha256': e['text_sha256'],
                      'original_to_model_boundaries': boundaries, 'policy': args.policy}
            if pid in passages and passages[pid] != record:
                raise ValueError('Conflicting passage snapshots')
            passages[pid] = record
            # The same physical occurrence may have several dictionary labels.
            # Predict once, but evaluate its labels separately by dictionary.
            target_id = sha(f'{pid}:{e["start_char"]}:{e["end_char"]}')
            targets[target_id] = {'target_id': target_id, 'passage_id': pid,
                'start': a, 'end': b, 'form': text[a:b],
                'original_start': e['start_char'], 'original_end': e['end_char']}
            cats = categories.get(e['segment_ref'])
            if not cats:
                raise ValueError('Missing categories')
            label = {'occurrence_id': e['example_id'], 'target_id': target_id,
                'gold_cluster': e['entry_key'], 'dictionary': e['dictionary'],
                'headword': e['headword'], 'ref': e['segment_ref'], 'categories': cats,
                'rule': e['evidence']['rule'], 'expert_verified': e['expert_verified']}
            assignments[(e['dictionary'], target_id)].add(e['entry_key'])
            labels.write(json.dumps(label, ensure_ascii=False)+'\n')
            counts['associations'] += 1
            dictionary_counts[e['dictionary']] += 1
            category_counts[cats[0]] += 1
    for name, rows in [('passages', passages.values()), ('targets', targets.values())]:
        with (args.output/(name+'.jsonl')).open('w') as out:
            for row in rows:
                out.write(json.dumps(row, ensure_ascii=False)+'\n')
    conflicts = [{'dictionary': d, 'target_id': t, 'entry_keys': sorted(keys)}
                 for (d, t), keys in sorted(assignments.items()) if len(keys) > 1]
    (args.output/'label_conflicts.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False)+'\n' for row in conflicts))
    lengths = sorted(len(p['text']) for p in passages.values())
    manifest = {'status': 'prepared_not_inferred', 'policy': args.policy,
        'source_sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
        'associations': counts['associations'], 'unique_targets': len(targets),
        'unique_passages': len(passages), 'within_dictionary_label_conflicts': len(conflicts), 'dictionaries': dict(dictionary_counts),
        'categories': dict(category_counts), 'max_passage_characters': max(lengths, default=0),
        'passages_with_editorial_brackets': sum('[' in p['text'] or '(' in p['text'] for p in passages.values()),
        'note': 'Character counts are not tokenizer lengths. Check model token budgets before inference. Gold labels are dictionary-derived, not expert gold.'}
    (args.output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False))


if __name__ == '__main__':
    main()
