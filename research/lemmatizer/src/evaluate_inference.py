"""Score saved predictions on repeated dictionary-specific reference clusters."""
import argparse
from collections import defaultdict, Counter
import hashlib
import json
from pathlib import Path
from evaluate_clusters import cluster_scores

MODELS = ('dicta', 'shoshan', 'stanza')


def read(path):
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def cohorts(labels, targets):
    """Deduplicate physical targets, exclude conflicting labels before filtering."""
    associations = defaultdict(dict)
    for row in labels:
        key = (row['dictionary'], row['target_id'])
        associations[key][row['gold_cluster']] = row
    conflicts = [key for key, entries in associations.items() if len(entries) > 1]
    groups = defaultdict(list)
    for entries in associations.values():
        if len(entries) == 1:
            row = next(iter(entries.values()))
            groups[(row['dictionary'], row['gold_cluster'])].append(row)
    selected = defaultdict(list)
    for (dictionary, _), rows in groups.items():
        if len(rows) < 2:
            continue
        selected[(dictionary, 'repeated')].extend(rows)
        if len({targets[r['target_id']]['form'] for r in rows}) > 1:
            selected[(dictionary, 'multiple_forms')].extend(rows)
    return selected, conflicts


def score(rows, predictions):
    gold, predicted = [], []
    reasons = Counter()
    for row in rows:
        target = row['target_id']
        pred = predictions[target]
        gold.append(row['gold_cluster'])
        if pred['status'] == 'ok':
            predicted.append(('lemma', pred['pred_cluster']))
        else:
            # Tagged tuples ensure abstentions cannot collide with real lemmas.
            predicted.append(('abstention', target))
            reasons[pred['reason']] += 1
    result = cluster_scores(gold, predicted)
    result.update(coverage=1 - sum(reasons.values()) / len(rows),
                  abstentions=sum(reasons.values()), abstention_reasons=dict(reasons))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--predictions', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    manifest = json.loads((args.predictions / 'manifest.json').read_text())
    for name, expected in manifest['input_hashes'].items():
        if sha(args.input / name) != expected:
            raise ValueError('Prediction input mismatch: ' + name)
    raw_targets = read(args.input / 'targets.jsonl')
    targets = {r['target_id']: r for r in raw_targets}
    if len(targets) != len(raw_targets):
        raise ValueError('Duplicate targets')
    predictions = {}
    for model in MODELS:
        rows = read(args.predictions / (model + '.jsonl'))
        indexed = {r['target_id']: r for r in rows}
        if len(indexed) != len(rows) or set(indexed) != set(targets):
            raise ValueError('Duplicate, missing or unexpected predictions: ' + model)
        for target, row in indexed.items():
            if row['model'] != model or row['form'] != targets[target]['form']:
                raise ValueError('Prediction identity mismatch')
            if row['status'] not in ('ok', 'abstained'):
                raise ValueError('Unknown prediction status')
            if (row['status'] == 'ok') != bool(row['pred_cluster']):
                raise ValueError('Inconsistent prediction status')
            if row['status'] == 'abstained' and not row['reason']:
                raise ValueError('Unexplained abstention')
        predictions[model] = indexed
    labels = read(args.input / 'labels.jsonl')
    selected, conflicts = cohorts(labels, targets)
    results = []
    membership = []
    for (dictionary, subset), rows in sorted(selected.items()):
        rows.sort(key=lambda r: (r['gold_cluster'], r['target_id']))
        membership.extend(dict(dictionary=dictionary, subset=subset,
                               target_id=r['target_id'], gold_cluster=r['gold_cluster']) for r in rows)
        for model in MODELS:
            results.append(dict(dictionary=dictionary, subset=subset, model=model,
                                **score(rows, predictions[model])))
    args.output.mkdir(parents=True, exist_ok=False)
    report = {'policy': 'repeated-reference-clusters-unique-abstentions-v1',
              'conflicting_dictionary_targets_excluded': len(conflicts),
              'conflicts': conflicts, 'results': results,
              'notes': ['Clusters are selected after deduplication and conflict exclusion, independently of predictions.',
                        'Multiple forms means distinct unpointed input spellings, including prefixes; not necessarily distinct inflections.',
                        'B3 averages per-occurrence precision and recall; F1 is their harmonic mean.',
                        'Scores describe the conservatively extracted dataset, not the library population. No bootstrap intervals yet.'],
              'hashes': {str(path.resolve()): sha(path) for path in
                         [args.input / 'labels.jsonl', args.input / 'targets.jsonl', args.predictions / 'manifest.json',
                          Path(__file__), Path(__file__).with_name('evaluate_clusters.py')] +
                         [args.predictions / (m + '.jsonl') for m in MODELS]}}
    (args.output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    with (args.output / 'membership.jsonl').open('w') as f:
        for row in membership:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    lines = ['# Dictionary-specific clustering evaluation', '',
             'Reference groups have at least two distinct occurrences. Each abstention is a unique singleton.',
             f'Excluded {len(conflicts)} dictionary/target pairs with conflicting reference labels before selecting groups.', '',
             '| Dictionary | Subset | Model | Occurrences | Groups | Coverage | B³ P | B³ R | B³ F1 |',
             '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for r in results:
        b = r['bcubed']
        lines.append(f"| {r['dictionary']} | {r['subset']} | {r['model']} | {r['n']} | {r['gold_clusters']} | {r['coverage']:.1%} | {b['precision']:.1%} | {b['recall']:.1%} | {b['f1']:.1%} |")
    lines += ['', 'These are provisional reference associations, not expert-adjudicated gold. No population-performance claim or uncertainty intervals.',
              'The JSON report includes pairwise scores; undefined pairwise denominators are null.', '']
    (args.output / 'report.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
