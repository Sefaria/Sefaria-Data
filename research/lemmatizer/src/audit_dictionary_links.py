"""Read-only link provenance inventory and seeded corpus-citation audit packet."""
import argparse
from collections import Counter, defaultdict
import hashlib,json,re
from pathlib import Path
from build_dataset import Backend,Store
from extraction_core import plain_text,find_spans,MATCH_MODES

TITLES={'BDB':'BDB Dictionary','BDB Aramaic':'BDB Aramaic Dictionary','Jastrow':'Jastrow Dictionary','Klein Dictionary':'Klein Dictionary'}
def title(ref):
    return next((t for t in TITLES if ref.startswith(t+', ')),None)
def rank(link):
    return hashlib.sha256(('20261004-links-v1:'+str(link['_id'])).encode()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str)+'\n')

def main():
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[4]/'Sefaria-Project');args=a.parse_args()
    args.output.mkdir(exist_ok=False,parents=True);store=Store(args.output);b=Backend(args.project,store)
    counts=Counter();frames=defaultdict(list)
    for link in b.db.links.find({'refs':{'$regex':r'^(Jastrow|Klein Dictionary|BDB)(,| |$)'}}):
        refs=link['refs'];ds=[r for r in refs if title(r)]
        kind='dictionary_to_dictionary' if len(ds)==2 else 'corpus_candidate' if len(ds)==1 and len(refs)==2 else 'other_frontmatter_or_shape'
        counts[(kind,str(link.get('generated_by')),str(link.get('type')))]+=1
        if kind=='corpus_candidate':frames[title(ds[0])].append(link)
    inventory={'scope':'BDB, BDB Aramaic, Jastrow and Klein; prefix-query also includes frontmatter. Other lexicons not audited.', 'counts':[{'kind':k[0],'generator':k[1],'type':k[2],'count':v} for k,v in counts.most_common()]}
    dump(args.output/'inventory.json',inventory)
    cases=[]
    for t,links in frames.items():
        used=set()
        for link in sorted(links,key=rank):
            dr=next(r for r in link['refs'] if title(r)==t);target=next(r for r in link['refs'] if r!=dr)
            # One example per dictionary entry, selection before any matching.
            entry_ref=re.sub(r' \d+(?::\d+)*(?:-\d+)?$','',dr)
            if entry_ref in used:continue
            used.add(entry_ref)
            c={'audit_id':f'L{len(cases)+1:03d}','dictionary':TITLES[t],'dictionary_ref':dr,'target_ref':target,'link':link,'passages':[],'candidates':[]}
            try:
                r=b.Ref(dr);entry=r.index_node.lexicon_entry
                c['entry']=entry.contents();c['entry_html']=entry.as_strings();c['definition']='\n'.join(plain_text(s) for s in c['entry_html'])
                c['citation_markup_contains_target']=any(target in s for s in c['entry_html'])
                ref=b.Ref(target)
                if getattr(ref.index_node,'is_virtual',False) or ref.is_book_level():raise ValueError('virtual or book-level target')
                segs=ref.all_segment_refs();c['target_segment_count']=len(segs)
                if len(segs)>20:raise ValueError('target exceeds 20-segment audit cap')
                c['passages']=[p for s in segs if (p:=b.passage(s.normal()))]
                wf=list(b.db.word_form.find({'lookups':{'$elemMatch':{'parent_lexicon':entry.parent_lexicon,'headword':entry.headword}}}).sort('_id',1).limit(201))
                c['wordforms_truncated']=len(wf)>200;wf=wf[:200]
                c['wordforms_considered']=[{'id':str(w['_id']),'form':w['form'],'generated_by':w.get('generated_by'),'cites_target':target in w.get('refs',[])} for w in wf]
                forms={entry.headword:'headword'}
                for w in wf:forms[w['form']]='wordform'
                for form,source in forms.items():
                    for mode in MATCH_MODES:
                        matches=[{'passage_id':p['passage_id'],'ref':p['ref'],'start_char':x,'end_char':y,'surface':p['text'][x:y]} for p in c['passages'] for x,y in find_spans(p['text'],form,mode)]
                        if matches:
                            c['candidates'].append({'form':form,'source':source,'method':mode,'matches':matches});break
            except (ValueError,KeyError,AttributeError,IndexError,b.InputError) as e:c['error']=str(e)
            cases.append(c)
            if len(used)==8:break
    with (args.output/'cases.jsonl').open('w') as f:
        for c in cases:f.write(json.dumps(c,ensure_ascii=False,default=str)+'\n')
    lines=['# Dictionary-link audit packet','', 'Seeded eight distinct entry refs per dictionary; sampled before matching. All selected outcomes retained.','']
    for c in cases:
        lines += [f"## {c['audit_id']} — {c['dictionary_ref']} → {c['target_ref']}",f"Generator: {c['link'].get('generated_by')}",'',c.get('definition',c.get('error','')),'']
        for p in c['passages']:lines += [p['ref']+': '+p['text'],'']
        lines += ['Candidates: '+json.dumps(c['candidates'],ensure_ascii=False),'']
    (args.output/'PACKET.md').write_text('\n'.join(lines))
    dump(args.output/'manifest.json',{'seed':'20261004-links-v1','selection':'Smallest seeded link hashes, one per dictionary entry ref, eight per dictionary; no outcome-based exclusions. Not disjoint from prior WordForm samples; not a statistical precision estimate.','cases':len(cases),'dictionary_corpus_link_counts':{k:len(v) for k,v in frames.items()},'inventory':inventory,'read_only':True})
    print(json.dumps({'cases':len(cases),'dictionary_corpus_link_counts':{k:len(v) for k,v in frames.items()},'inventory':inventory}))
    store.db.close()

if __name__=='__main__':main()
