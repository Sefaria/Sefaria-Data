"""Score judged offline retrieval runs; unknown relevance is never silently zero."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
from evaluate_inference import read, sha


def score_hits(hits, judgments, k):
    top=hits[:k]
    known=[h['doc_id'] in judgments for h in top]
    positives={d for d,g in judgments.items() if g>0}
    complete=bool(judgments) and all(known)
    result={'retrieved':len(hits),'judged_top_k':sum(known),'top_k_complete':complete,
            'precision_at_k':None,'ndcg_at_k':None,'recall_of_judged_positives':None}
    if complete:
        grades=[judgments[h['doc_id']] for h in top]
        result['precision_at_k']=sum(g>0 for g in grades)/k
        ideal=sorted(judgments.values(),reverse=True)[:k]
        dcg=lambda gs:sum((2**g-1)/math.log2(i+2) for i,g in enumerate(gs))
        if dcg(ideal)>0:result['ndcg_at_k']=dcg(grades)/dcg(ideal)
    if positives:
        result['recall_of_judged_positives']=len({h['doc_id'] for h in hits}&positives)/len(positives)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',type=Path,required=True)
    p.add_argument('--judgments',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--k',type=int,default=10)
    args=p.parse_args()
    if args.k<1:p.error('k must be positive')
    runs=read(args.runs);judged=defaultdict(dict);seen=set()
    for j in read(args.judgments):
        key=(j['query_id'],j['doc_id'])
        if key in seen:raise ValueError('Duplicate judgment')
        seen.add(key)
        grade=j.get('relevance')
        if grade is None:continue
        if type(grade) is not int or not 0<=grade<=3:raise ValueError('Use integer relevance 0–3, or null for unjudged')
        judged[j['query_id']][j['doc_id']]=grade
    output=[];seen_runs=set()
    for r in runs:
        key=(r['query_id'],r['mode'])
        if key in seen_runs or r['mode'] not in ('baseline','enhanced'):raise ValueError('Invalid/duplicate run')
        if len({h['doc_id'] for h in r['hits']})!=len(r['hits']):raise ValueError('Duplicate ranked document')
        seen_runs.add(key)
        output.append({'query_id':r['query_id'],'mode':r['mode'],**score_hits(r['hits'],judged[r['query_id']],args.k)})
    query_ids={r['query_id'] for r in runs}
    if seen_runs!={(q,m) for q in query_ids for m in ['baseline','enhanced']}:raise ValueError('Unpaired runs')
    if set(judged)-query_ids:raise ValueError('Judgments for unknown queries')
    metrics={}
    for metric in ['precision_at_k','ndcg_at_k','recall_of_judged_positives']:
        usable={q for q in query_ids if all(r[metric] is not None for r in output if r['query_id']==q)}
        means={mode:sum(r[metric] for r in output if r['mode']==mode and r['query_id'] in usable)/len(usable) if usable else None for mode in ['baseline','enhanced']}
        metrics[metric]={'paired_queries':len(usable),'means':means,
                         'enhanced_minus_baseline':means['enhanced']-means['baseline'] if usable else None}
    report={'k':args.k,'queries':len(query_ids),'judged_pairs':sum(map(len,judged.values())),
            'aggregate':metrics,'per_query':output,
            'notes':['0=irrelevant, 1=marginal, 2=relevant, 3=highly relevant.',
                     'P@k and nDCG@k withheld when any returned top-k result is unjudged.',
                     'nDCG ideal and recall use the judged pool, not exhaustive corpus relevance.',
                     'Aggregate comparisons use identical eligible queries for both modes.'],
            'hashes':{'runs':sha(args.runs),'judgments':sha(args.judgments),'code':sha(Path(__file__))}}
    if args.output.exists():raise ValueError('Output exists')
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(metrics,indent=2))

if __name__=='__main__':main()
