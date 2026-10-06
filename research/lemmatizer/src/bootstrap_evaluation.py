"""Paired reference-cluster bootstrap of saved B3 scores (no new inference)."""
import argparse
from collections import Counter, defaultdict
from itertools import combinations
import json
from pathlib import Path
import numpy as np
from tqdm import tqdm
from evaluate_inference import MODELS, read, sha


def prepare(rows, predictions, groups):
    gi = {g:i for i,g in enumerate(groups)}
    cells = Counter()
    sizes = np.zeros(len(groups))
    covered = np.zeros(len(groups))
    pi = {}
    for row in rows:
        g = gi[row['gold_cluster']]
        pred = predictions[row['target_id']]
        label = ('lemma', pred['pred_cluster']) if pred['status']=='ok' else ('abstention', row['target_id'])
        p = pi.setdefault(label, len(pi))
        cells[g,p] += 1
        sizes[g] += 1
        covered[g] += pred['status']=='ok'
    g, p, n = zip(*[(g,p,n) for (g,p),n in cells.items()])
    return np.array(g), np.array(p), np.array(n), sizes, covered, len(pi)


def weighted_scores(data, weights):
    g, p, n, sizes, covered, npred = data
    mass = weights[g] * n
    total = np.dot(weights, sizes)
    predicted_sizes = np.bincount(p, weights=mass, minlength=npred)
    gold_sizes = weights[g] * sizes[g]
    active = mass > 0
    precision = np.sum(mass[active] ** 2 / predicted_sizes[p[active]]) / total
    recall = np.sum(mass[active] ** 2 / gold_sizes[active]) / total
    f1 = 2 * precision * recall / (precision + recall)
    return np.array([precision, recall, f1, np.dot(weights, covered) / total])


def interval(values):
    return np.quantile(values, [.025,.975]).tolist()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation',type=Path,required=True)
    parser.add_argument('--predictions',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replicates',type=int,default=2000)
    parser.add_argument('--seed',type=int,default=20261005)
    args=parser.parse_args()
    if args.replicates < 2: parser.error('At least two replicates required')
    original=json.loads((args.evaluation/'report.json').read_text())
    predictions={}
    for model in MODELS:
        path=args.predictions/(model+'.jsonl')
        if sha(path)!=original['hashes'][str(path.resolve())]:
            raise ValueError('Predictions changed since evaluation')
        predictions[model]={r['target_id']:r for r in read(path)}
    cohorts=defaultdict(list)
    for row in read(args.evaluation/'membership.jsonl'):
        cohorts[row['dictionary'],row['subset']].append(row)
    rng=np.random.default_rng(args.seed)
    records=[]
    samples={}
    for (dictionary,subset),rows in sorted(cohorts.items()):
        groups=sorted({r['gold_cluster'] for r in rows})
        data=[prepare(rows,predictions[m],groups) for m in MODELS]
        points=np.array([weighted_scores(d,np.ones(len(groups))) for d in data])
        for i,model in enumerate(MODELS):
            prior=next(r for r in original['results'] if (r['dictionary'],r['subset'],r['model'])==(dictionary,subset,model))
            expected=[prior['bcubed'][k] for k in ['precision','recall','f1']]+[prior['coverage']]
            np.testing.assert_allclose(points[i],expected,rtol=1e-12)
        draws=np.empty((args.replicates,len(MODELS),4))
        for b in tqdm(range(args.replicates),desc=dictionary+' / '+subset):
            weights=rng.multinomial(len(groups),np.full(len(groups),1/len(groups)))
            for i,d in enumerate(data): draws[b,i]=weighted_scores(d,weights)
        key=f'cohort_{len(records)}'
        samples[key]=draws
        scores={model:{metric:{'point':float(points[i,j]),'ci95':interval(draws[:,i,j])}
                       for j,metric in enumerate(['precision','recall','f1','coverage'])}
                for i,model in enumerate(MODELS)}
        differences={}
        for i,j in combinations(range(len(MODELS)),2):
            delta=draws[:,i,2]-draws[:,j,2]
            differences[MODELS[i]+' - '+MODELS[j]]={
                'point':float(points[i,2]-points[j,2]),'ci95':interval(delta),
                'fraction_positive':float(np.mean(delta>0)), 'fraction_tied':float(np.mean(delta==0))}
        records.append(dict(dictionary=dictionary,subset=subset,groups=len(groups),occurrences=len(rows),
                            samples_key=key,scores=scores,f1_differences=differences))
    args.output.mkdir(parents=True,exist_ok=False)
    report=dict(seed=args.seed,replicates=args.replicates,method='paired multinomial reference-group bootstrap; percentile 95% intervals',
                notes=['Sample G reference groups with replacement within each dictionary/subset; retain every occurrence in sampled groups.',
                       'Multiplicity is an observation weight. Retain original reference and prediction identities, including each target-specific abstention label. Do not invent new lexical identities for duplicated groups.',
                       'Recompute weighted contingency tables and B3 on every replicate. Identical weights are shared by all models.',
                       'Conditional on this extracted dataset. Does not correct selection bias or account for dependence across groups sharing passages/works.',
                       'Pairwise intervals are unadjusted for multiple comparisons. Fraction positive is not a posterior probability or a p-value.',
                       'Very small cohorts, especially Klein multiple_forms (four groups), give fragile uncertainty estimates.'],
                hashes={str(p.resolve()):sha(p) for p in [args.evaluation/'report.json',args.evaluation/'membership.jsonl',Path(__file__)]},
                numpy_version=np.__version__,model_order=MODELS,metric_order=['precision','recall','f1','coverage'],results=records)
    (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    np.savez_compressed(args.output/'replicates.npz',**samples)
    lines=['# Paired cluster bootstrap','',f'{args.replicates:,} replicates; seed {args.seed}. Percentile 95% intervals.','',
           '| Dictionary | Subset | Model | B³ F1 | 95% interval |','|---|---|---|---:|---:|']
    for r in records:
        for model,s in r['scores'].items():
            f=s['f1'];lo,hi=f['ci95']
            lines.append(f"| {r['dictionary']} | {r['subset']} | {model} | {f['point']:.1%} | {lo:.1%}–{hi:.1%} |")
    lines+=['','## Paired F1 differences','','Values are percentage points; positive favors the first model.','',
            '| Dictionary | Subset | Comparison | Difference | 95% interval |','|---|---|---|---:|---:|']
    for r in records:
        for pair,s in r['f1_differences'].items():
            lo,hi=s['ci95']
            lines.append(f"| {r['dictionary']} | {r['subset']} | {pair} | {100*s['point']:.2f} | {100*lo:.2f}–{100*hi:.2f} |")
    lines+=['']+report['notes']
    (args.output/'report.md').write_text('\n'.join(lines)+'\n')
    print('Saved '+str(args.output/'report.md'))


if __name__=='__main__': main()
