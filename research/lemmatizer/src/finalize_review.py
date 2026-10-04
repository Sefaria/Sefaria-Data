"""Validate externally authored review labels, join features, and summarize.

Does NOT assign judgments or fit a model. Uncertain and absent proposals are
excluded from binary model examples, and manual recoveries stay separate.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from extraction_core import stable_id


def read(path):
    return [json.loads(l) for l in path.read_text().splitlines()]


def indexed(rows, key):
    result={}
    for r in rows:
        if r[key] in result: raise ValueError('Duplicate '+key)
        result[r[key]]=r
    return result


def finalize(root):
    cases=indexed(read(root/'cases.jsonl'),'case_id')
    annotations=indexed(read(root/'annotations.jsonl'),'case_id')
    features=indexed(read(root/'features.jsonl'),'case_id')
    if set(cases)!=set(annotations) or set(cases)!=set(features):
        raise ValueError('Case/annotation/feature IDs must match exactly')
    # Known overlap groups: entries, WordForms, or frozen passages in common.
    parent={k:k for k in cases}
    def find(k):
        while parent[k]!=k:
            parent[k]=parent[parent[k]];k=parent[k]
        return k
    seen={}
    for cid,c in cases.items():
        keys=[('entry',c['entry_id']),('form',c['word_form_id'])]+[('passage',p['passage_id']) for p in c['passages']]
        for key in keys:
            if key in seen:parent[find(cid)]=find(seen[key])
            else:seen[key]=cid
    members=defaultdict(list)
    for cid in cases:members[find(cid)].append(cid)
    groups={cid:stable_id('group',sorted(v)) for v in members.values() for cid in v}
    counts=Counter(); by_dictionary=defaultdict(Counter); by_method=defaultdict(Counter)
    model_rows=[]; ledger=[]
    for cid,c in cases.items():
        a=annotations[cid]
        if a['review_id']!=c['review_id'] or not a.get('reason'):
            raise ValueError('Invalid annotation identity or missing reason')
        if a['association_label'] not in {'correct','incorrect','uncertain','not_assessable'}:
            raise ValueError('Invalid association label')
        if c['occurrence'] is None:
            if a['alignment_label']!='not_proposed' or a['association_label']!='not_assessable':
                raise ValueError('Do not label an absent proposal as a binary prediction')
        elif a['alignment_label'] not in {'correct','incorrect','uncertain'}:
            raise ValueError('Invalid alignment label')
        label=a['association_label'];counts[label]+=1
        by_dictionary[c['dictionary']][label]+=1
        by_method[c['features']['match_method']][label]+=1
        if c['occurrence'] and label in {'correct','incorrect'} and a['alignment_label']=='correct':
            model_rows.append({'case_id':cid,'review_id':c['review_id'],'overlap_group':groups[cid],
                'features':{k:v for k,v in features[cid].items() if k not in {'case_id','review_id'}},
                'association_target':int(label=='correct'),'label_source':'assistant_reviewed_not_expert_verified'})
        ledger.append({'case_id':cid,'review_id':c['review_id'],'overlap_group':groups[cid],**a})
    recoveries=read(root/'manual_recoveries.jsonl') if (root/'manual_recoveries.jsonl').exists() else []
    for r in recoveries:
        c=cases[r['case_id']]
        if c['occurrence'] is not None:raise ValueError('Recovery must refer to absent proposal')
        p=next(p for p in c['passages'] if p['passage_id']==r['passage_id'])
        if p['text'][r['start_char']:r['end_char']]!=r['surface']:raise ValueError('Recovery span mismatch')
    rules={}
    for name,predicate in {
        'unique_span':lambda f:f['matches_in_source_ref']==1,
        'unique_span_single_entry_in_dictionary':lambda f:f['matches_in_source_ref']==1 and f['same_dictionary_entry_candidates']==1,
        'unique_span_pointing_preserved':lambda f:f['matches_in_source_ref']==1 and f['match_method'] in {'exact','cantillation_insensitive'},
    }.items():
        selected=[cid for cid,c in cases.items() if c['occurrence'] and predicate(c['features'])]
        rules[name]={'kept_cases':len(selected),'review_labels':dict(Counter(annotations[cid]['association_label'] for cid in selected))}
    summary={'cases':len(cases),'target_entries':len({c['entry_id'] for c in cases.values()}),
             'proposed_cases':sum(c['occurrence'] is not None for c in cases.values()),
             'association_labels':dict(counts),'by_dictionary':by_dictionary,'by_method':by_method,
             'binary_model_examples':len(model_rows),'known_overlap_groups':len(members),
             'manual_recovery_spans':len(recoveries),'manual_recovery_cases':len({r['case_id'] for r in recoveries}),
             'recovery_labels':dict(Counter(r['association_label'] for r in recoveries)),
             'rule_audit_in_sample_only':rules,
             'limitations':'One assistant reviewer, not blind to entry/provenance; no expert adjudication, model training, held-out validation, calibrated probabilities, or corpus-wide precision estimate. Case counts overweight repeated forms and entries.'}
    (root/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    for name,rows in [('model_examples.jsonl',model_rows),('review_ledger.jsonl',ledger)]:
        (root/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    manifest=json.loads((root/'manifest.json').read_text());manifest.update(label_status='assistant_review_complete',has_labels=True,review_protocol='contextual-v1',reviewer_count=1)
    (root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    lines=['# Reviewed WordForm sample', '', f"**{len(cases)} cases across {summary['target_entries']} sampled dictionary entries. These are provisional assistant judgments, not expert gold labels.**",'',
      'Entries were selected before matching, by seeded hash within dictionary/generator strata. All selected attempts were retained, including failures and repeated positions.', '',
      '## Review results', '', '| Association judgment | Cases |','|---|---:|']
    lines += [f'| {label} | {count} |' for label,count in sorted(counts.items())]
    lines += ['',f"There were {summary['proposed_cases']} proposed spans. Alignment labels describe whether the displayed surface form was located correctly; association labels separately assess whether that word belongs to the target entry. `not_assessable` means no span was proposed, not an incorrect lemma prediction.", '',
      f"The review also recorded {len(recoveries)} manually located spans in {summary['manual_recovery_cases']} failed cases. These do not replace the original proposals or enter the baseline model examples.", '',
      '## Contextual findings', '', 'See [FINDINGS.md](FINDINGS.md) for the reviewer-authored observations, if present. The ledger below preserves every individual judgment.', '',
      '## Observable features and later modeling', '',
      f"`features.jsonl` contains extraction-time features for all cases. `model_examples.jsonl` contains {len(model_rows)} proposed, binary-labeled cases only; reasons, judgments and recovered spans are excluded from input features. There are {len(members)} known overlap groups across the full sample.", '',
      'Features cover dictionary/generator, matching tier, span ambiguity, candidate-entry ambiguity, pointing, source-ref frequency, fallback use, definition length, and whether entry markup explicitly cites the source ref. A citation is supporting evidence, not independent confirmation.', '',
      'No model has been trained. Future splits must keep overlap groups together and also check near-duplicate quotations and cross-dictionary equivalences. Do not infer calibration or population precision from these in-sample judgments.', '',
      '## Simple rule audit (same sample; not held-out performance)', '', '| Rule | Retained cases | Correct | Incorrect | Uncertain |','|---|---:|---:|---:|---:|']
    for name,r in rules.items():
        c=r['review_labels'];lines.append(f"| {name} | {r['kept_cases']} | {c.get('correct',0)} | {c.get('incorrect',0)} | {c.get('uncertain',0)} |")
    lines += ['', '## Complete annotation ledger', '', 'Full definitions and passage contexts: [PACKET.md](PACKET.md). The source dataset path is recorded in manifest.json.', '',
      '| Case | Ref | Entry | Association | Reason |', '|---|---|---|---|---|']
    for cid,c in cases.items():
        a=annotations[cid]
        lines.append(f"| {c['review_id']} | {c['source_ref']} | {c['dictionary']}: {c['headword']} | {a['association_label']} | {a['reason']} |")
    (root/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);a=p.parse_args();finalize(a.directory)
