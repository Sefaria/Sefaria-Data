"""Freeze one primary Hebrew version per Tanakh/Rashi/Mishnah work, read-only Mongo export."""
import argparse
from collections import Counter
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
from build_dataset import Backend
from extraction_core import ranked_hebrew_versions


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,default=Path('/Users/yon/projects/sefaria/Sefaria-Project'))
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--include-mishnah',action='store_true')
    p.add_argument('--extend',type=Path,help='Preserve an existing corpus snapshot and add new works only')
    args=p.parse_args()
    from evaluate_inference import sha, read
    previous=json.loads((args.extend/'manifest.json').read_text()) if args.extend else None
    if previous and sha(args.extend/'documents.jsonl')!=previous['documents_sha256']:
        raise ValueError('Existing corpus hash mismatch')
    b=Backend(args.project,None)
    from sefaria.model import library, IndexSet, RefData
    from sefaria.search import TextIndexer, get_exact_english_analyzer
    from tqdm import tqdm
    bases=list(library.get_indexes_in_corpus('Tanakh',full_records=True))
    base_titles={i.title for i in bases}
    rashis=[i for i in IndexSet({'collective_title':'Rashi','categories':'Tanakh'})
            if set(getattr(i,'base_text_titles',[])) & base_titles]
    if len(bases)!=39: raise ValueError(f'Expected 39 Tanakh books, found {len(bases)}; inspect corpus metadata')
    mishnah=list(library.get_indexes_in_corpus('Mishnah',full_records=True)) if args.include_mishnah else []
    if args.include_mishnah and len(mishnah)!=63:
        raise ValueError(f'Expected 63 Mishnah tractates; found {len(mishnah)}')
    indices=sorted(bases+rashis+mishnah,key=lambda i:i.title)
    selections=list(previous['version_selections']) if previous else []
    previous_titles={v['work'] for v in selections}
    if previous_titles-set(i.title for i in indices):raise ValueError('Extension must retain all previous works')
    chosen=[]
    for index in indices:
        if index.title in previous_titles:continue
        versions=ranked_hebrew_versions(list(b.db.texts.find({'title':index.title})))
        if not versions or not versions[0].get('isPrimary'): raise ValueError('No primary Hebrew version: '+index.title)
        v=versions[0]
        selections.append({'work':index.title,'version_id':str(v['_id']),'version_title':v['versionTitle'],
                           'priority':v.get('priority'),'isPrimary':v.get('isPrimary'),
                           'language':v.get('language'),'languageFamilyName':v.get('languageFamilyName'),
                           'license':v.get('license'),'categories':index.categories})
        chosen.append((index,v))
    args.output.mkdir(parents=True,exist_ok=False)
    ranks={r['ref']:r.get('pagesheetrank',RefData.DEFAULT_PAGESHEETRANK) for r in b.db.ref_data.find({}, {'ref':1,'pagesheetrank':1})}
    counts=Counter(previous['counts'] if previous else {}); skipped=Counter(previous.get('empty_segments',{}) if previous else {}); seen=set()
    with (args.output/'documents.jsonl').open('w') as out:
        if args.extend:
            for row in read(args.extend/'documents.jsonl'):
                if row['ref'] in seen:raise ValueError('Duplicate existing ref')
                seen.add(row['ref']); out.write(json.dumps(row,ensure_ascii=False)+'\n')
        for index,version in tqdm(chosen,desc='Export new works',unit='work'):
            def action(raw,tref,he_tref,v):
                content=TextIndexer.modify_text_in_doc(raw)
                if not content.strip(): skipped[index.title]+=1;return
                if tref in seen: raise ValueError('Duplicate ref '+tref)
                seen.add(tref)
                docid=hashlib.sha256((str(version['_id'])+'\0'+tref).encode()).hexdigest()
                row={'doc_id':docid,'ref':tref,'heRef':he_tref,'work':index.title,
                     'version':version['versionTitle'],'version_id':str(version['_id']),
                     'lang':version['language'],'categories':index.categories,
                     'path':'/'.join(index.categories+[index.title]),
                     'pagesheetrank':ranks.get(tref,RefData.DEFAULT_PAGESHEETRANK),
                     'exact':content,'naive_lemmatizer':content,
                     'text_sha256':hashlib.sha256(content.encode()).hexdigest()}
                out.write(json.dumps(row,ensure_ascii=False)+'\n'); counts[index.title]+=1
            b.Version(version).walk_thru_contents(action)
    from evaluate_inference import sha
    manifest={'policy':'one-primary-hebrew-version-per-work-v1','base_works':len(bases),'rashi_works':len(rashis),'mishnah_works':len(mishnah),
              'extended_from':str(args.extend) if args.extend else None,
              'previous_manifest':previous,
              'documents':sum(counts.values()),'counts':dict(counts),'empty_segments':dict(skipped),
              'version_selections':selections,'segment_fallback':False,
              'source':'local Mongo snapshot; not a production ES export',
              'project_commit':subprocess.check_output(['git','-C',str(args.project),'rev-parse','HEAD'],text=True).strip(),
              'documents_sha256':sha(args.output/'documents.jsonl'),
              'exporter_sha256':sha(Path(__file__)),
              'cleanup_source':inspect.getsource(TextIndexer.modify_text_in_doc),
              'footnote_source':inspect.getsource(TextIndexer.remove_footnotes),
              'baseline_exact_analyzer':get_exact_english_analyzer()}
    (args.output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:manifest[k] for k in ['documents','base_works','rashi_works','mishnah_works']}))

if __name__=='__main__':main()
