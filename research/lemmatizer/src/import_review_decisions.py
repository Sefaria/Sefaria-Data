"""Expand explicitly authored TSV review decisions; never infer semantic labels.

TSV columns: numeric review IDs/ranges, association label, reason code, reason.
Every case must have exactly one authored decision. The reviewer is responsible
for checking alignment as well as association before using this importer.
"""
import argparse
from datetime import date
import json
from pathlib import Path


def convert(root):
    decisions={}
    for line in (root/'reviewer_decisions.tsv').read_text().splitlines():
        ids,label,code,reason=line.split('\t',3)
        for block in ids.split(','):
            bounds=list(map(int,block.split('-')))
            for number in range(bounds[0],bounds[-1]+1):
                key=f'R{number:03d}'
                if key in decisions:raise ValueError('Duplicate decision '+key)
                decisions[key]=(label,code,reason)
    cases=[json.loads(l) for l in (root/'cases.jsonl').read_text().splitlines()]
    if set(decisions)!={c['review_id'] for c in cases}:raise ValueError('Decision IDs do not cover exactly all cases')
    rows=[]
    for c in cases:
        label,code,reason=decisions[c['review_id']]
        if (c['occurrence'] is None)!=(label=='not_assessable'):
            raise ValueError('Proposal/label mismatch '+c['review_id'])
        rows.append({'case_id':c['case_id'],'review_id':c['review_id'],
            'alignment_label':'correct' if c['occurrence'] else 'not_proposed',
            'association_label':label,'reason_code':code,'reason':reason,
            'evidence_entry_id':c['entry_id'],'evidence_passage_ids':[p['passage_id'] for p in c['passages']],
            'reviewer':'assistant','reviewed_on':date.today().isoformat(),'review_protocol':'contextual-v1',
            'expert_verified':False})
    with (root/'annotations.jsonl').open('x') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print('Imported explicit decisions:',len(rows))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);a=p.parse_args();convert(a.directory)
