"""Create review cases and pre-review features from a completed extraction.

Only selected seed entries are review targets. Other dictionary associations are
preserved in extraction output, but never silently treated as reviewed labels.
"""
import argparse
from collections import defaultdict
import json
import re
from pathlib import Path
import unicodedata
from extraction_core import plain_text, stable_id


def load(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def definition_text(entry):
    result = []
    def walk(obj):
        if isinstance(obj, dict):
            for k,v in obj.items():
                if k == 'definition' and isinstance(v,str):
                    result.append(plain_text(v))
                elif isinstance(v,(dict,list)):
                    walk(v)
        elif isinstance(obj,list):
            for item in obj:walk(item)
    walk(entry.get('content',{}))
    return '\n'.join(result)


def cited_refs(value):
    if isinstance(value, str):
        return set(re.findall(r"data-ref=[\"']([^\"']+)[\"']", value))
    if isinstance(value, dict):
        return set().union(*(cited_refs(v) for v in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(cited_refs(v) for v in value)) if value else set()
    return set()


def has_pointing(text):
    return any('\u0590' <= c <= '\u05ff' and unicodedata.category(c).startswith('M') for c in text)


def prepare(dataset, out):
    out.mkdir(parents=True,exist_ok=False)
    manifest = json.loads((dataset/'manifest.json').read_text())
    assert manifest['status']=='complete'
    targets = {'entry:'+eid for e in manifest['selected_entries'] for eid in e['entry_ids']}
    entries = {e['entry_id']:e for e in load(dataset/'entries.jsonl')}
    forms = {w['word_form_id']:w for w in load(dataset/'word_forms.jsonl')}
    passages = {p['passage_id']:p for p in load(dataset/'passages.jsonl')}
    occurrences = {o['occurrence_id']:o for o in load(dataset/'occurrences.jsonl')}
    cases = []
    for attempt in load(dataset/'attempts.jsonl'):
        w = forms[attempt['word_form_id']]
        resolved = {eid for l in w['resolved_lookups'] for eid in l['entry_ids']}
        for eid in sorted(resolved & targets):
            for oid in attempt['candidate_occurrence_ids'] or [None]:
                occurrence = occurrences.get(oid)
                contexts = [passages[occurrence['passage_id']]] if occurrence else [passages[pid] for pid in attempt['searched_passage_ids']]
                if occurrence:
                    association = next(a for a in occurrence['associations'] if a['word_form_id']==w['word_form_id'] and a['entry_id']==eid and a['source_ref']==attempt['source_ref'])
                else:
                    association = None
                entry = entries[eid]
                same_dictionary = {i for i in resolved if entries[i]['dictionary']==entry['dictionary']}
                feature = {
                    'entry_definition_length':len(definition_text(entry['entry_snapshot'])),
                    'entry_explicitly_cites_source_ref':attempt['source_ref'] in (cited_refs(entry['entry_snapshot']) | set(entry['entry_snapshot'].get('refs',[]))),
                    'dictionary':entry['dictionary'], 'generator':w['source_record'].get('generated_by','<missing>'),
                    'attempt_status':attempt['status'], 'has_proposed_span':occurrence is not None,
                    'match_method':attempt['match_method'] or 'none',
                    'matches_in_source_ref':len(attempt['candidate_occurrence_ids']),
                    'same_dictionary_entry_candidates':len(same_dictionary),
                    'all_dictionary_entry_candidates':len(resolved),
                    'lookup_resolution_count':association['lookup_resolution_count'] if association else None,
                    'form_has_pointing':has_pointing(w['source_record']['form']),
                    'headword_has_pointing':has_pointing(entry['headword']),
                    'form_length':len(w['source_record']['form']),
                    'form_word_count':len(w['source_record']['form'].split()),
                    'source_ref_count':w['total_distinct_refs'],
                    'partial_text_coverage':attempt['partial_text_coverage'],
                    'uses_fallback':any(p['is_fallback'] for p in contexts),
                    'literal_surface_equal':occurrence['surface']==w['source_record']['form'] if occurrence else None,
                    'surface_has_pointing':has_pointing(occurrence['surface']) if occurrence else None,
                }
                cases.append({'case_id':stable_id('case',eid,w['word_form_id'],attempt['source_ref'],oid),
                    'entry_id':eid, 'dictionary':entry['dictionary'], 'headword':entry['headword'],
                    'definition':definition_text(entry['entry_snapshot']),
                    'word_form_id':w['word_form_id'], 'word_form':w['source_record']['form'],
                    'source_ref':attempt['source_ref'], 'occurrence':occurrence, 'passages':contexts,
                    'attempt':attempt, 'features':feature})
    cases.sort(key=lambda c:(c['dictionary'],c['headword'],c['source_ref'],c['word_form'],c['case_id']))
    for i,c in enumerate(cases,1):c['review_id']=f'R{i:03d}'
    (out/'cases.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases))
    (out/'features.jsonl').write_text(''.join(json.dumps({'case_id':c['case_id'],'review_id':c['review_id'],**c['features']},ensure_ascii=False)+'\n' for c in cases))
    (out/'manifest.json').write_text(json.dumps({'dataset':str(dataset),'case_count':len(cases),'target_entry_count':len(targets),
        'sampling':'All sampled attempts, all proposed positions, restricted to selected seed entries; failures retained as separate diagnostic cases.',
        'label_status':'unreviewed','features_version':'observable-v1','has_labels':False},ensure_ascii=False,indent=2))
    lines=['# Review packet', '', 'Unreviewed cases. Full passages and definitions are in cases.jsonl.', '']
    last=None
    for c in cases:
        if c['entry_id']!=last:
            lines += ['## '+c['dictionary']+' — '+c['headword'],'',c['definition'],'']
            last=c['entry_id']
        o=c['occurrence']
        text='[no passage available]'
        if o:
            p=c['passages'][0];a,b=o['start_char'],o['end_char']
            text=p['text'][max(0,a-150):a]+' **'+p['text'][a:b]+'** '+p['text'][b:b+150]
        elif c['passages']:
            text='\n'.join(p['text'] for p in c['passages'])
        lines += [f"### {c['review_id']} · {c['source_ref']} · form {c['word_form']}",
                  f"{c['features']['attempt_status']} / {c['features']['match_method']} / {c['features']['generator']}",'',text,'']
    (out/'PACKET.md').write_text('\n'.join(lines))
    print(json.dumps({'cases':len(cases),'entries':len({c['entry_id'] for c in cases}),
                     'proposed_spans':sum(c['occurrence'] is not None for c in cases)}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dataset',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();prepare(a.dataset,a.output)
