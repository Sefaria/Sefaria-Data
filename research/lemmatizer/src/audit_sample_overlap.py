"""Verify exported sample disjointness from prior extraction snapshots."""
import argparse
import json
from pathlib import Path


def keys(directory):
    def rows(name):
        return [json.loads(line) for line in (directory/(name+'.jsonl')).read_text().splitlines()]
    return {'entry_ids':{e['entry_id'] for e in rows('entries')},
            'dictionary_headwords':{(e['dictionary'],e['headword']) for e in rows('entries')},
            'word_form_ids':{w['word_form_id'] for w in rows('word_forms')},
            'source_refs':{a['source_ref'] for a in rows('attempts')},
            'segment_refs':{p['ref'] for p in rows('passages')},
            'passage_text_hashes':{p['text_sha256'] for p in rows('passages')}}


def audit(dataset, priors):
    current=keys(dataset)
    comparisons=[]
    for prior in priors:
        previous=keys(prior)
        overlap={key:sorted(current[key] & previous[key]) for key in current}
        comparisons.append({'prior_dataset':str(prior),'overlap_counts':{k:len(v) for k,v in overlap.items()},'overlaps':overlap})
    return {'dataset':str(dataset),'passed':all(not any(c['overlap_counts'].values()) for c in comparisons),
            'comparisons':comparisons,'scope':'Exact IDs, dictionary/headword pairs, source refs, expanded passage refs and whole-passage text hashes. Does not establish independence of paraphrases, embedded quotations, or equivalent lexemes across dictionaries. Candidate refs were also expanded before sampling to exclude overlaps with prior attempted refs.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dataset',type=Path);p.add_argument('--prior',action='append',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=audit(a.dataset,a.prior)
    with a.output.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result))
    if not result['passed']:raise SystemExit(1)
