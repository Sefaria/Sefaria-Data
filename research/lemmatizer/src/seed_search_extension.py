"""Seed an expanded corpus checkpoint with verified, unchanged existing annotations."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
from evaluate_inference import read, sha


def validate_reuse(old_docs,new_docs,annotations):
    old={r['doc_id']:r for r in old_docs};new={r['doc_id']:r for r in new_docs}
    if len(old)!=len(old_docs) or len(new)!=len(new_docs):raise ValueError('Duplicate corpus IDs')
    for key,row in old.items():
        if new.get(key)!=row:raise ValueError('Existing document changed: '+key)
    seen=set()
    for row in annotations:
        key=row['doc_id']
        if key in seen or key not in old:raise ValueError('Duplicate or unexpected annotation')
        if row['text_sha256']!=old[key]['text_sha256']:raise ValueError('Annotation text changed')
        seen.add(key)
    if seen!=set(old):raise ValueError('Source annotations are incomplete')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-corpus',type=Path,required=True)
    p.add_argument('--source-lemmas',type=Path,required=True)
    p.add_argument('--corpus',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    identity=json.loads((args.source_lemmas/'manifest.json').read_text())
    if identity['corpus']!=sha(args.source_corpus/'documents.jsonl'):raise ValueError('Source identity mismatch')
    for name,digest in identity['code'].items():
        if sha(Path(__file__).with_name(name))!=digest:raise ValueError('Inference code changed: '+name)
    corpus_meta=json.loads((args.corpus/'manifest.json').read_text())
    corpus_hash=sha(args.corpus/'documents.jsonl')
    if corpus_hash!=corpus_meta['documents_sha256']:raise ValueError('Expanded corpus hash mismatch')
    old=read(args.source_corpus/'documents.jsonl');new=read(args.corpus/'documents.jsonl')
    annotations=read(args.source_lemmas/'lemmas.jsonl')
    validate_reuse(old,new,annotations)
    args.output.mkdir(parents=True,exist_ok=False)
    identity['corpus']=corpus_hash
    with sqlite3.connect(args.output/'checkpoint.sqlite') as db:
        db.executescript('CREATE TABLE meta(data TEXT); CREATE TABLE docs(id TEXT PRIMARY KEY,data TEXT);')
        db.execute('INSERT INTO meta VALUES (?)',(json.dumps(identity),))
        db.executemany('INSERT INTO docs VALUES (?,?)',((r['doc_id'],json.dumps(r,ensure_ascii=False)) for r in annotations))
    (args.output/'manifest.json').write_text(json.dumps(identity,indent=2)+'\n')
    provenance={'source_corpus':str(args.source_corpus),'source_lemmas':str(args.source_lemmas),
                'source_lemmas_sha256':sha(args.source_lemmas/'lemmas.jsonl'),
                'source_manifest_sha256':sha(args.source_lemmas/'manifest.json'),
                'seed_script_sha256':sha(Path(__file__)),
                'reused_documents':len(old),'new_documents':len(new)-len(old)}
    (args.output/'seed_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(provenance))

if __name__=='__main__':main()
