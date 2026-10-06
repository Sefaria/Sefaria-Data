"""Offline, resumable inference for Dicta, Shoshan and Stanza; no scoring or gold input."""
import argparse
from collections import Counter
import fcntl
from functools import lru_cache
import gc
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import sqlite3
import time

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT/'models'
os.environ['HF_HOME'] = str(MODELS/'hf_cache')
os.environ['HF_MODULES_CACHE'] = str(MODELS/'hf_modules')
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
from inference_adapters import Adapter, AlignmentError, common_window


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def dump(path, data):
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    tmp.replace(path)


def export(db, output):
    totals = {}
    for model in ['dicta','shoshan','stanza']:
        counts = Counter()
        tmp = output/(model+'.jsonl.tmp')
        with tmp.open('w') as f:
            for (raw,) in db.execute('SELECT data FROM predictions WHERE model=? ORDER BY target_id',(model,)):
                row=json.loads(raw)
                counts[row['reason'] or 'ok']+=1
                f.write(raw+'\n')
        tmp.replace(output/(model+'.jsonl'))
        totals[model]=dict(counts)
    dump(output/'summary.json',totals)
    print(json.dumps(totals),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True,help='Prepared benchmark directory')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--model',choices=['all','dicta','shoshan','stanza'],default='all')
    parser.add_argument('--device',choices=['cpu','mps'],default='mps')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--limit',type=int,help='Same deterministic first N targets for each model; omit for full run')
    args=parser.parse_args()
    if args.limit is not None and args.limit<1:parser.error('--limit must be positive')
    if args.resume:
        if not (args.output/'predictions.sqlite').exists():parser.error('No checkpoint to resume')
    else:args.output.mkdir(parents=True,exist_ok=False)
    with (args.output/'.run.lock').open('w') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:parser.error('Output is already in use')
        import torch
        from transformers import AutoTokenizer
        from shoshan.normalize import normalize_text
        from tqdm import tqdm
        if args.device=='mps' and not torch.backends.mps.is_available():parser.error('Apple MPS unavailable; choose --device cpu')
        config=json.loads((ROOT/'configs/comparison.json').read_text())
        manifest=json.loads((args.input/'manifest.json').read_text())
        if manifest['policy']!='unpointed-v1':parser.error('Runner currently supports unpointed-v1 only')
        installation=json.loads((ROOT/'configs/model-installation.json').read_text())
        print('Verifying pinned local model files...',flush=True)
        for name,info in installation['downloaded_files'].items():
            if digest(MODELS/name)!=info['sha256']:raise ValueError('Model file changed: '+name)
        identity={'input_hashes':{name:digest(args.input/name) for name in ['passages.jsonl','targets.jsonl']},
            'source_hashes':{name:digest(Path(__file__).with_name(name)) for name in
                ['run_inference.py','inference_adapters.py','benchmark_core.py']},
            'model_config':{k:config[k] for k in ['dicta','shoshan','stanza']},
            'model_installation_sha256':digest(ROOT/'configs/model-installation.json'),
            'versions':{n:version(n) for n in ['torch','transformers','stanza','shoshan','tokenizers']},
            'device':args.device,'policy':manifest['policy'],'context_policy':'shared-greedy-whole-word-v1'}
        db=sqlite3.connect(args.output/'predictions.sqlite')
        db.executescript('''CREATE TABLE IF NOT EXISTS metadata(id INTEGER PRIMARY KEY,data TEXT);
            CREATE TABLE IF NOT EXISTS predictions(model TEXT,target_id TEXT,data TEXT,PRIMARY KEY(model,target_id));
            CREATE TABLE IF NOT EXISTS windows(target_id TEXT PRIMARY KEY,data TEXT);''')
        previous=db.execute('SELECT data FROM metadata WHERE id=1').fetchone()
        if previous and json.loads(previous[0])!=identity:raise ValueError('Run inputs, code, models or device changed; use a new output')
        db.execute('INSERT OR IGNORE INTO metadata VALUES (1,?)',(json.dumps(identity),));db.commit()
        dump(args.output/'manifest.json',identity)
        passages={r['passage_id']:r for r in map(json.loads,(args.input/'passages.jsonl').open())}
        targets=list(map(json.loads,(args.input/'targets.jsonl').open()))
        if len({t['target_id'] for t in targets})!=len(targets):raise ValueError('Duplicate targets')
        targets=sorted(targets,key=lambda t:t['target_id'])[:args.limit]
        for t in targets:
            p=passages[t['passage_id']]
            if hashlib.sha256(p['text'].encode()).hexdigest()!=p['text_sha256']:raise ValueError('Passage hash mismatch')
            if p['text'][t['start']:t['end']]!=t['form']:raise ValueError('Target span mismatch')
        dt=AutoTokenizer.from_pretrained(MODELS/'dicta',local_files_only=True)
        st=AutoTokenizer.from_pretrained(MODELS/'shoshan/model/encoder',local_files_only=True)
        @lru_cache(maxsize=8192)
        def fits(text):
            return (len(dt(text,truncation=False,verbose=False)['input_ids'])<=512 and
                    len(st(normalize_text(text),truncation=False,verbose=False)['input_ids'])<=160)
        try:
            for t in tqdm(targets,desc='Prepare shared contexts',unit='target'):
                if db.execute('SELECT 1 FROM windows WHERE target_id=?',(t['target_id'],)).fetchone():continue
                text=passages[t['passage_id']]['text']
                try:
                    a,b=common_window(text,t['start'],t['end'],fits)
                    row={'start':a,'end':b,'text':text[a:b],
                         'target_start':t['start']-a,'target_end':t['end']-a,'reason':None,
                         'dicta_tokens':len(dt(text[a:b],truncation=False)['input_ids']),
                         'shoshan_tokens':len(st(normalize_text(text[a:b]),truncation=False)['input_ids'])}
                except AlignmentError as error:row={'reason':str(error)}
                db.execute('INSERT INTO windows VALUES (?,?)',(t['target_id'],json.dumps(row,ensure_ascii=False)))
                db.commit()
            chosen=['dicta','shoshan','stanza'] if args.model=='all' else [args.model]
            for name in chosen:
                done={r[0] for r in db.execute('SELECT target_id FROM predictions WHERE model=?',(name,))}
                pending=[t for t in targets if t['target_id'] not in done]
                if not pending:continue
                # Share nearby targets' identical contexts through an adapter cache.
                pending.sort(key=lambda t:(t['passage_id'],t['start']))
                print('Loading '+name+' on '+args.device+'...',flush=True)
                adapter=Adapter(name,MODELS,config,args.device)
                for t in tqdm(pending,total=len(targets),initial=len(targets)-len(pending),desc=name,unit='target'):
                    w=json.loads(db.execute('SELECT data FROM windows WHERE target_id=?',(t['target_id'],)).fetchone()[0])
                    row={'model':name,'target_id':t['target_id'],'passage_id':t['passage_id'],
                         'form':t['form'],'original_start':t['original_start'],'original_end':t['original_end'],
                         'model_start':t['start'],'model_end':t['end'],'window':w,'raw_lemma':None,
                         'pred_cluster':None,'reason':w['reason'],'status':'abstained'}
                    began=time.monotonic()
                    if not w['reason']:
                        try:
                            row.update(adapter.predict(w['text'],w['target_start'],w['target_end']))
                            row['reason']=row.get('reason') or (None if row['pred_cluster'] else 'empty_prediction')
                            row['status']='ok' if row['pred_cluster'] is not None else 'abstained'
                        except AlignmentError as error:row['reason']=str(error)
                    row['elapsed_seconds']=round(time.monotonic()-began,5)
                    db.execute('INSERT INTO predictions VALUES (?,?,?)',(name,t['target_id'],json.dumps(row,ensure_ascii=False)))
                    db.commit()  # Each target is durable, including an abstention.
                adapter.tokens.cache_clear()
                del adapter
                gc.collect()
                if args.device=='mps':torch.mps.empty_cache()
                export(db,args.output)
            dump(args.output/'run_status.json',{'status':'complete_for_selection','selected_targets':len(targets),
                 'available_targets':manifest['unique_targets'],'models':chosen,'limit':args.limit})
        except BaseException as error:
            db.rollback()
            dump(args.output/'run_status.json',{'status':'interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',
                 'error':type(error).__name__+': '+str(error),'resume':'Use the same output with --resume'})
            raise
        finally:
            export(db,args.output)
            db.close()


if __name__=='__main__':main()
