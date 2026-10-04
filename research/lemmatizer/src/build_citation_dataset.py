"""Conservative citation-first extractor over frozen dictionary-link audit records.

No WordForms or review labels are read. Input includes raw links, entry content,
and primary-Hebrew passage snapshots produced by audit_dictionary_links.py.
"""
import argparse,json,re,unicodedata
from pathlib import Path
from html import unescape
from extraction_core import find_spans,plain_text,stable_id,sha

VERSION='citation-rules-v2'
MODES=('exact','cantillation_insensitive','exact_maqaf','cantillation_insensitive_maqaf')
ANCHOR=re.compile(r'<a\b[^>]*data-ref=[\"\']([^\"\']+)[\"\'][^>]*>.*?</a>',re.S)
SPAN=re.compile(r'<span\b[^>]*dir=[\"\']rtl[\"\'][^>]*>(.*?)</span>',re.S)

def definitions(obj,path='content'):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k=='definition' and isinstance(v,str):yield path+'.definition',v
            elif isinstance(v,(dict,list)):yield from definitions(v,path+'.'+k)
    elif isinstance(obj,list):
        for i,v in enumerate(obj):yield from definitions(v,f'{path}[{i}]')

def legacy_evidence(case):
    entry=case.get('entry',{}); hw=entry.get('headword','')
    for path,html in definitions(entry.get('content',{})):
        anchors=[m for m in ANCHOR.finditer(html) if unescape(m[1])==case['target_ref']]
        for a in anchors:
            # A single explicitly printed BDB inflection immediately before its citation.
            before=html[:a.start()]; spans=list(SPAN.finditer(before))
            if case['dictionary'].startswith('BDB') and spans:
                s=spans[-1]; form=plain_text(s[1]); lead=plain_text(before[max(0,s.start()-80):s.start()])
                if not plain_text(before[s.end():]).strip() and re.search(r'(?:sf\.|emph\.|abs\.|cstr\.)\s*$',lead) and re.fullmatch(r'[\u0591-\u05bd\u05bf\u05c1\u05c2\u05c4\u05c5\u05c7\u05d0-\u05ea]+',form):
                    yield {'rule':'explicit_inflection_before_citation','form':form,'definition_path':path,'definition_html':html,'citation_html':a.group(),'evidence_html':s.group()}
            # Klein noun explicitly identified as occurring in this verse. No guessed inflection.
            if case['dictionary']=='Klein Dictionary' and 'n.' in entry.get('content',{}).get('morphology','') and re.search(r'\boccurring\b',plain_text(html)):
                if re.fullmatch(r'[\u0591-\u05bd\u05bf\u05c1\u05c2\u05c4\u05c5\u05c7\u05d0-\u05ea]+',hw):
                    yield {'rule':'klein_explicit_noun_attestation','form':hw,'definition_path':path,'definition_html':html,'citation_html':a.group(),'evidence_html':hw}

HEBREW_WORD=re.compile(r'[\u05d0-\u05ea][\u0591-\u05bd\u05bf\u05c1\u05c2\u05c4\u05c5\u05c7\u05d0-\u05ea]*')
VOWEL=re.compile(r'[\u05b0-\u05bb\u05c7]')

def evidence(case):
    yield from legacy_evidence(case)
    for path,html in definitions(case.get('entry',{}).get('content',{})):
        for anchor in ANCHOR.finditer(html):
            if unescape(anchor[1])!=case['target_ref']:continue
            base={'definition_path':path,'definition_html':html,'citation_html':anchor.group()}
            before=html[:anchor.start()]
            spans=list(SPAN.finditer(before))
            if case['dictionary'].startswith('BDB') and spans:
                s=spans[-1];form=plain_text(s[1]);lead=plain_text(before[max(0,s.start()-100):s.start()])
                # Only a closed sequence of grammatical labels may intervene.
                grammar=r'(?:Pf\.|Impf\.|Imv\.|Inf\.|Pt\.|pl\.|mpl\.|fpl\.)\s*(?:(?:[123]|m\.?|f\.?|s\.?|pl\.|mpl\.|fpl\.|ms\.|fs\.|act\.|pass\.|abs\.|cstr\.)\s*)*$'
                correction=re.match(r'^\s*\([^)]*\b(?:but|read)\b',plain_text(html[anchor.end():]),re.I)
                if (not correction and not plain_text(before[s.end():]).strip() and re.search(grammar,lead)
                    and HEBREW_WORD.fullmatch(form)):
                    yield {**base,'rule':'explicit_grammatical_form_before_citation','form':form,'evidence_html':s.group()}
            if case['dictionary']=='Jastrow Dictionary':
                # Jastrow often points only the lexical target within a quotation.
                # Require an immediately following, complete multiword quotation.
                tail=html[anchor.end():];s=SPAN.match(tail.lstrip())
                if not s:continue
                quote=plain_text(s[1]);words=list(HEBREW_WORD.finditer(quote))
                if not 2<=len(words)<=8 or re.sub(HEBREW_WORD,'',quote).strip():continue
                pointed=[i for i,w in enumerate(words) if VOWEL.search(w[0])]
                if len(pointed)!=1:continue
                i=pointed[0]
                yield {**base,'rule':'jastrow_pointed_target_in_citation_quote',
                    'form':words[i][0],'quote':quote,'quote_word_index':i,'evidence_html':s.group()}

def pointing_compatible(form,surface):
    def clusters(text):
        out=[]
        for ch in unicodedata.normalize('NFD',text):
            if '\u05d0'<=ch<='\u05ea':out.append([ch,set()])
            elif out and (VOWEL.fullmatch(ch) or ch in '\u05bc\u05c1\u05c2'):out[-1][1].add(ch)
        return out
    a,b=clusters(form),clusters(surface)
    return len(a)==len(b) and all(x[0]==y[0] and x[1]<=y[1] for x,y in zip(a,b))

def evidence_matches(case,ev):
    if 'quote' in ev:
        for p in case['passages']:
            for a,b in find_spans(p['text'],ev['quote'],'vowel_insensitive_maqaf'):
                words=list(HEBREW_WORD.finditer(p['text'][a:b]))
                source_words=list(HEBREW_WORD.finditer(ev['quote']))
                if len(words)!=len(source_words):continue
                w=words[ev['quote_word_index']]
                if pointing_compatible(ev['form'],w[0]):
                    yield p,a+w.start(),a+w.end(),'quote_consonants_target_pointing'
        return
    for mode in MODES:
        matches=[(p,a,b,mode) for p in case['passages'] for a,b in find_spans(p['text'],ev['form'],mode)]
        if matches:
            yield from matches
            return
    # Only conjunction waw; retain all stem vowels and consonants.
    # Run only after ordinary matching fails, and return the complete host word.
    if not VOWEL.search(ev['form']) or len(re.findall(r'[\u05d0-\u05ea]',ev['form']))<2:return
    for p in case['passages']:
        for word in HEBREW_WORD.finditer(p['text']):
            prefix=re.match(r'^ו[\u0591-\u05bd\u05bf\u05c1\u05c2\u05c4\u05c5\u05c7]*',word[0])
            if not prefix:continue
            rest=word[0][prefix.end():]
            if find_spans(rest,ev['form'],'cantillation_insensitive')==[(0,len(rest))]:
                # Reuse original full-word boundary validation (blocks abbreviations).
                if (word.start(),word.end()) in find_spans(p['text'],word[0],'exact'):
                    yield p,word.start(),word.end(),'conjunction_waw_pointing_preserved'

def extract(case):
    if case.get('error'):
        return None, 'source_retrieval_error'
    if not case.get('passages'):
        return None, 'missing_primary_hebrew_text'
    proposals=[];evs=list(evidence(case))
    for ev in evs:
        proposals.extend((p,a,b,ev,mode) for p,a,b,mode in evidence_matches(case,ev))
    positions={(p['passage_id'],a,b) for p,a,b,ev,mode in proposals}
    if len(positions)!=1:
        return None, 'no_supported_evidence_rule' if not evs else 'no_pointing_preserving_match' if not positions else 'multiple_candidate_positions'
    p,a,b,ev,mode=proposals[0]
    return {'example_id':stable_id('citation-example',stable_id('entry-key',case['dictionary'],case['entry']['headword']),p['passage_id'],a,b),
        'entry_key':stable_id('entry-key',case['dictionary'],case['entry']['headword']),
        'entry_identity_policy':'dictionary plus exact headword; source snapshot did not retain Mongo _id',
        'entry_snapshot':case['entry'],'link_snapshot':case['link'],'headword':case['entry']['headword'],'dictionary':case['dictionary'],
        'dictionary_ref':case['dictionary_ref'],'link_id':str(case['link']['_id']), 'source_ref':case['target_ref'],
        'audit_id':case['audit_id'],'passage_id':p['passage_id'],'segment_ref':p['ref'],
        'version_id':p['version_id'],'version_title':p['version_title'],'is_fallback':p['is_fallback'],
        'text':p['text'],'text_sha256':sha(p['text']),'start_char':a,'end_char':b,'surface':p['text'][a:b],
        'match_method':mode,'rule_version':VERSION,'evidence':ev,
        'supporting_evidence':[e for _,_,_,e,_ in proposals],
        'acceptance':'deterministic_rule','expert_verified':False},None

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--per-dictionary',type=int,default=4)
    args=parser.parse_args()
    if args.per_dictionary<1:parser.error('per-dictionary must be positive')
    args.output.mkdir(parents=True,exist_ok=False)
    cases=[json.loads(l) for l in args.input.read_text().splitlines()];counts={};examples={};attempts=[]
    for c in cases:
        d=c['dictionary']
        if counts.get(d,0)>=args.per_dictionary:continue
        counts[d]=counts.get(d,0)+1
        ex,reason=extract(c)
        if ex:examples[ex['example_id']]=ex
        attempts.append({'audit_id':c['audit_id'],'dictionary_ref':c['dictionary_ref'],'target_ref':c['target_ref'],'status':'accepted' if ex else 'skipped','reason':reason,'example_id':ex['example_id'] if ex else None})
    for name,rows in [('examples',examples.values()),('attempts',attempts)]:
        (args.output/(name+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    manifest={'rule_version':VERSION,'input':str(args.input.resolve()),'input_sha256':sha(args.input.read_text()),'script_sha256':sha(Path(__file__).read_text()),'sample_selection':'first N per dictionary in the already seeded link-audit order; development smoke test, not held-out evaluation','attempts':len(attempts),'accepted':len(examples),'skipped':sum(a['status']=='skipped' for a in attempts),'rules_use_wordforms':False,'rules_use_review_labels':False}
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    lines=['# Citation-first pilot','',f"{len(attempts)} links, {len(examples)} accepted examples. Development sample; precision not established.",'']
    for e in examples.values():
        a,b=e['start_char'],e['end_char'];lines += [f"## {e['dictionary_ref']} → {e['segment_ref']}",e['text'][:a]+' **'+e['surface']+'** '+e['text'][b:],'',e['evidence']['rule']+' / '+e['match_method'],'',plain_text(e['evidence']['definition_html']),'']
    lines += ['## All attempts','']+[f"- {a['audit_id']}: {a['status']} — {a['reason'] or a['example_id']}" for a in attempts]
    (args.output/'REPORT.md').write_text('\n'.join(lines))
    print(json.dumps(manifest))

if __name__=='__main__':main()
