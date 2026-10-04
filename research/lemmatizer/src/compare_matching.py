"""Replay matching against frozen passages; never copies old labels to new spans."""
import argparse
import json
from pathlib import Path
from extraction_core import MATCH_MODES, MATCHING_VERSION, find_spans


def compare(dataset):
    def rows(name):
        return [json.loads(line) for line in (dataset/(name+'.jsonl')).read_text().splitlines()]
    forms = {w['word_form_id']:w['source_record']['form'] for w in rows('word_forms')}
    passages = {p['passage_id']:p for p in rows('passages')}
    occurrences = {o['occurrence_id']:o for o in rows('occurrences')}
    changes=[]; lost=0; added=0
    for a in rows('attempts'):
        old={(occurrences[o]['passage_id'],occurrences[o]['start_char'],occurrences[o]['end_char']) for o in a['candidate_occurrence_ids']}
        new=set(); method=None
        for mode in MATCH_MODES:
            new={(pid,start,end) for pid in a['searched_passage_ids'] for start,end in find_spans(passages[pid]['text'],forms[a['word_form_id']],mode)}
            if new:
                method=mode;break
        if old != new:
            lost += len(old-new); added += len(new-old)
            changes.append({'word_form_id':a['word_form_id'],'source_ref':a['source_ref'],'form':forms[a['word_form_id']], 'old_method':a['match_method'],'new_method':method,
                'added':[{'ref':passages[p]['ref'],'start_char':s,'end_char':e,'surface':passages[p]['text'][s:e]} for p,s,e in sorted(new-old)],'removed':sorted(old-new)})
    return {'dataset':str(dataset),'matching_version':MATCHING_VERSION,'changed_attempts':len(changes),'added_spans':added,'removed_spans':lost,'changes':changes,'note':'Matching regression comparison only; added spans are unreviewed, not positive labels.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dataset',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=compare(a.dataset)
    with a.output.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='changes'}))
