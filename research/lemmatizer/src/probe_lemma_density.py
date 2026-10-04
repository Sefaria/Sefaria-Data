"""Expand all links of already recovered lemmas to measure cluster density.

This is a conditioned cohort, not a corpus-wide yield forecast. No WordForms/LLMs.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import time
from audit_dictionary_links import title
from build_dataset import Backend, Store
from build_citation_dataset import evidence, extract, VERSION


def entry_ref(ref):
    return re.sub(r' \d+(?::\d+)*(?:-\d+)?$', '', ref)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--examples',type=Path,nargs='+',required=True,
        help='Accepted examples JSONL files defining the conditioned cohort')
    parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[4]/'Sefaria-Project')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    start=time.monotonic();root=Path(__file__).resolve().parents[1]
    cohort={}
    for path in args.examples:
        for line in path.read_text().splitlines():
            e=json.loads(line);cohort[entry_ref(e['dictionary_ref'])]=e
    store=Store(args.output);backend=Backend(args.project,store)
    counts=Counter();by_entry=defaultdict(Counter);examples={};attempts=[]
    for link in backend.db.links.find({'refs':{'$regex':r'^(Jastrow|Klein Dictionary|BDB)(,| |$)'}}):
        refs=link.get('refs',[]);ds=[r for r in refs if title(r)]
        if len(refs)!=2 or len(ds)!=1 or entry_ref(ds[0]) not in cohort:continue
        dr=ds[0];key=entry_ref(dr);seed=cohort[key];target=next(r for r in refs if r!=dr)
        counts['links']+=1;by_entry[key]['links']+=1
        case={'audit_id':'D'+str(counts['links']), 'dictionary':seed['dictionary'],
            'dictionary_ref':dr,'target_ref':target,'link':link,
            'entry':seed['entry_snapshot'],'passages':[]}
        if not list(evidence(case)):
            reason='no_supported_evidence_rule';example=None
        else:
            counts['links_with_evidence']+=1
            try:
                ref=backend.Ref(target)
                if getattr(ref.index_node,'is_virtual',False) or ref.is_book_level():raise ValueError('broad/virtual target')
                segments=ref.all_segment_refs()
                if len(segments)>100:raise ValueError('segment cap')
                for segment in segments:
                    p=backend.passage(segment.normal())
                    if p:case['passages'].append(p)
                    else:raise ValueError('missing segment')
            except (ValueError,KeyError,AttributeError,IndexError,backend.InputError) as error:
                case['error']=str(error)
            example,reason=extract(case)
        if example:
            examples[example['example_id']]=example;counts['accepted_links']+=1
        else:counts[reason]+=1
        attempts.append({'entry_ref':key,'link_id':str(link['_id']),'target_ref':target,
            'accepted':bool(example),'reason':reason})
    grouped=defaultdict(list)
    for e in examples.values():grouped[entry_ref(e['dictionary_ref'])].append(e)
    rows=[]
    for key,seed in cohort.items():
        ee=grouped[key]
        rows.append({'entry_ref':key,'dictionary':seed['dictionary'],
            'links':by_entry[key]['links'],'occurrences':len(ee),
            'distinct_surfaces':len({e['surface'] for e in ee}),
            'distinct_unpointed_forms':len({re.sub(r'[\u0591-\u05c7]','',e['surface']) for e in ee}),
            'refs':[e['segment_ref'] for e in ee]})
    report={'rule_version':VERSION,'scope':'All corpus links of dictionary entries already accepted in two 1000-link samples; conditioned on prior success, not a representative corpus sample.',
        'cohort_lemmas':len(cohort),'counts':dict(counts),'unique_examples':len(examples),
        'lemmas_with_2plus':sum(r['occurrences']>=2 for r in rows),
        'lemmas_with_3plus':sum(r['occurrences']>=3 for r in rows),
        'lemmas_with_5plus':sum(r['occurrences']>=5 for r in rows),
        'lemmas_with_multiple_unpointed_forms':sum(r['distinct_unpointed_forms']>=2 for r in rows),
        'occurrence_distribution':dict(Counter(r['occurrences'] for r in rows)),
        'elapsed_seconds':round(time.monotonic()-start,2),
        'lemmas':sorted(rows,key=lambda r:(-r['occurrences'],r['entry_ref']))}
    (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for name,data in [('examples',examples.values()),('attempts',attempts)]:
        (args.output/(name+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False,default=str)+'\n' for r in data))
    store.db.close()
    print(json.dumps({k:v for k,v in report.items() if k!='lemmas'},ensure_ascii=False))


if __name__=='__main__':main()
