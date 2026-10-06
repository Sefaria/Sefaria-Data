"""Resumable offline every-token lemmatization for the search corpus."""
import argparse
from collections import Counter
import fcntl
from importlib.metadata import version
import json
from pathlib import Path
import sqlite3
from evaluate_inference import sha, read
from search_lemma_core import FullTextLemmatizer


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--limit',type=int)
    p.add_argument('--resume',action='store_true')
    p.add_argument('--device',choices=['mps','cpu'],default='mps')
    p.add_argument('--batch-docs',type=int,default=16)
    args=p.parse_args()
    if args.batch_docs<1 or args.limit is not None and args.limit<1:p.error('Limits must be positive')
    if args.resume:
        if not (args.output/'checkpoint.sqlite').exists():p.error('No checkpoint')
    else:args.output.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[1]
    install=json.loads((root/'configs/model-installation.json').read_text())
    for path,info in install['downloaded_files'].items():
        if path.startswith('shoshan/') and sha(root/'models'/path)!=info['sha256']:raise ValueError('Model hash mismatch')
    identity={'corpus':sha(args.input/'documents.jsonl'),'device':args.device,
              'batch_docs':args.batch_docs,'model_installation':sha(root/'configs/model-installation.json'),
              'versions':{n:version(n) for n in ['torch','transformers','shoshan','tokenizers']},
              'code':{n:sha(Path(__file__).with_name(n)) for n in ['lemmatize_search_corpus.py','search_lemma_core.py','benchmark_core.py']}}
    manifest=json.loads((args.input/'manifest.json').read_text())
    if identity['corpus']!=manifest['documents_sha256']:raise ValueError('Corpus changed')
    with (args.output/'.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        db=sqlite3.connect(args.output/'checkpoint.sqlite')
        db.executescript('CREATE TABLE IF NOT EXISTS meta(data TEXT); CREATE TABLE IF NOT EXISTS docs(id TEXT PRIMARY KEY,data TEXT);')
        old=db.execute('SELECT data FROM meta').fetchone()
        if old and json.loads(old[0])!=identity:raise ValueError('Resume identity changed; use a new output')
        if not old:db.execute('INSERT INTO meta VALUES (?)',(json.dumps(identity),));db.commit()
        (args.output/'manifest.json').write_text(json.dumps(identity,indent=2)+'\n')
        corpus=sorted(read(args.input/'documents.jsonl'),key=lambda r:r['doc_id'])[:args.limit]
        done={r[0] for r in db.execute('SELECT id FROM docs')}
        pending=[r for r in corpus if r['doc_id'] not in done]
        from tqdm import tqdm
        try:
            if pending:
                model=FullTextLemmatizer(args.device)
                with tqdm(total=len(corpus),initial=len(corpus)-len(pending),desc='Lemmatize full passages',unit='passage') as bar:
                    for i in range(0,len(pending),args.batch_docs):
                        batch=pending[i:i+args.batch_docs]
                        annotated=model.annotate([r['exact'] for r in batch])
                        for row,ann in zip(batch,annotated):
                            ann.update(doc_id=row['doc_id'],text_sha256=row['text_sha256'])
                            db.execute('INSERT INTO docs VALUES (?,?)',(row['doc_id'],json.dumps(ann,ensure_ascii=False)))
                        db.commit();bar.update(len(batch))
        finally:
            db.rollback();counts=Counter();n=0
            tmp=args.output/'lemmas.jsonl.tmp'
            with tmp.open('w') as f:
                for (raw,) in db.execute('SELECT data FROM docs ORDER BY id'):
                    f.write(raw+'\n'); row=json.loads(raw);n+=1
                    counts.update(t['reason'] or 'ok' for t in row['tokens'])
            tmp.replace(args.output/'lemmas.jsonl')
            report={'documents':n,'available_documents':manifest['documents'],'tokens':sum(counts.values()),'outcomes':dict(counts)}
            (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps(report));db.close()

if __name__=='__main__':main()
