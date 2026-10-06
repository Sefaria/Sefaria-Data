"""Local-only ES baseline/lemma comparison. Never touches shared or production indexes."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from evaluate_inference import read, sha


def request(url, method='GET', body=None, ndjson=False):
    data=body.encode() if ndjson else (json.dumps(body).encode() if body is not None else None)
    req=Request(url,data=data,method=method,headers={'Content-Type':'application/x-ndjson' if ndjson else 'application/json'})
    try:
        with urlopen(req,timeout=120) as resp:return json.load(resp)
    except HTTPError:
        raise  # Preserve HTTP status handling, especially index-not-found.
    except URLError as error:
        raise ConnectionError(
            f'Cannot connect to local Elasticsearch at {urlparse(url).netloc}: {error.reason}. '
            'Start it with: docker compose -f research/lemmatizer/offline_search/compose.yaml up -d '
            'and wait for it to become ready. Saved lemmas are unaffected.'
        ) from error


def check_destination(url,index):
    parsed=urlparse(url)
    if parsed.scheme!='http' or parsed.hostname not in ('localhost','127.0.0.1') or parsed.port!=19200:
        raise ValueError('This POC only permits http://localhost:19200 or http://127.0.0.1:19200')
    if not re.fullmatch(r'lemma-poc-[a-z0-9-]+',index):raise ValueError('Index must start lemma-poc- and contain lowercase letters/digits/hyphens')


def query_body(query, lemmas=None, weight=1., size=50, slop=10):
    # Match ordinary frontend search by default; slop=0 retains strict phrases.
    if isinstance(slop, bool) or not isinstance(slop, int) or not 0 <= slop <= 50:
        raise ValueError("Slop must be an integer from 0 to 50")
    query=re.sub(r'(\S)"(\S)',r'\1״\2',query)
    baseline={'match_phrase':{'naive_lemmatizer':{'query':query,'slop':slop,'_name':'baseline'}}}
    core=baseline
    if lemmas and weight > 0:
        core={'bool':{'should':[baseline,{'match_phrase':{'shoshan_lemma':{'query':lemmas,'slop':slop,'boost':weight,'_name':'lemma'}}}], 'minimum_should_match':1}}
    return {'size':size,'track_total_hits':True,
            'query':{'function_score':{'query':core,'field_value_factor':{'field':'pagesheetrank','missing':.04}}},
            'sort':[{'_score':'desc'},{'doc_id':'asc'}],
            '_source':['doc_id','ref','version','work','exact','categories']}


def load(args):
    corpus_manifest=json.loads((args.corpus/'manifest.json').read_text())
    lemma_manifest=json.loads((args.lemmas/'manifest.json').read_text())
    corpus_hash=sha(args.corpus/'documents.jsonl')
    if corpus_hash!=corpus_manifest['documents_sha256'] or corpus_hash!=lemma_manifest['corpus']:
        raise ValueError('Corpus identity mismatch')
    docs=read(args.corpus/'documents.jsonl');annotations=read(args.lemmas/'lemmas.jsonl')
    anns={r['doc_id']:r for r in annotations}
    if len(anns)!=len(annotations):raise ValueError('Duplicate annotations')
    ids={r['doc_id'] for r in docs}
    if len(ids)!=len(docs) or set(anns)-ids:raise ValueError('Document identity mismatch')
    if set(anns)!=ids and not args.allow_partial:raise ValueError('Lemmatization incomplete; only smoke tests may use --allow-partial')
    docs=[r for r in docs if r['doc_id'] in anns]
    if not docs:raise ValueError('Empty selection')
    for r in docs:
        a=anns[r['doc_id']]
        if a['text_sha256']!=r['text_sha256']:raise ValueError('Text mismatch')
        if a['shoshan_lemma']!=' '.join(t['lemma'] for t in a['tokens']):raise ValueError('Corrupt lemma sequence')
    try:
        request(args.url+'/'+args.index)
    except HTTPError as e:
        if e.code!=404:raise
    else:raise ValueError('Index already exists; choose a fresh name (no automatic deletion)')
    provenance={'corpus_sha256':corpus_hash,'lemmas_sha256':sha(args.lemmas/'lemmas.jsonl'),
                'lemma_pipeline':lemma_manifest,'documents':len(docs),'partial':len(docs)!=len(ids),'status':'loading'}
    mapping={'_meta':provenance,'dynamic':False,'properties':{
        'doc_id':{'type':'keyword'},'ref':{'type':'keyword'},'work':{'type':'keyword'},
        'categories':{'type':'keyword'},'path':{'type':'keyword'},'version':{'type':'keyword'},
        'pagesheetrank':{'type':'double','index':False},
        'exact':{'type':'text','analyzer':'exact_english'},
        'naive_lemmatizer':{'type':'text','analyzer':'sefaria-naive-lemmatizer',
                            'search_analyzer':'sefaria-naive-lemmatizer-less-prefixes',
                            'fields':{'exact':{'type':'text','analyzer':'exact_english'}}},
        'shoshan_lemma':{'type':'text','analyzer':'whitespace'}}}
    settings={'number_of_shards':1,'number_of_replicas':0,
              'analysis':{'analyzer':{'exact_english':corpus_manifest['baseline_exact_analyzer']}}}
    request(args.url+'/'+args.index,'PUT',{'settings':settings,'mappings':mapping})
    from tqdm import tqdm
    for start in tqdm(range(0,len(docs),250),desc='Index passages',unit='batch'):
        lines=[]
        for row in docs[start:start+250]:
            row=dict(row,shoshan_lemma=anns[row['doc_id']]['shoshan_lemma'])
            lines += [json.dumps({'create':{'_index':args.index,'_id':row['doc_id']}}),json.dumps(row,ensure_ascii=False)]
        result=request(args.url+'/_bulk','POST','\n'.join(lines)+'\n',True)
        if result.get('errors'):raise RuntimeError('Bulk indexing failed: '+str([i for i in result['items'] if i['create'].get('error')][:2]))
    request(args.url+'/'+args.index+'/_refresh','POST')
    count=request(args.url+'/'+args.index+'/_count')['count']
    if count!=len(docs):raise ValueError('Indexed document count mismatch')
    provenance['status']='ready'
    request(args.url+'/'+args.index+'/_mapping','PUT',{'_meta':provenance})
    print(json.dumps({'index':args.index,'documents':count,'partial':provenance['partial']}))


def compare(args):
    from search_lemma_core import FullTextLemmatizer
    index_info=request(args.url+'/'+args.index)
    meta=index_info[args.index]['mappings']['_meta']
    if meta['status']!='ready':raise ValueError('Index build incomplete')
    # Reject query/document preprocessing drift, including model version drift.
    root=Path(__file__).resolve().parents[1]
    for name in ['search_lemma_core.py','benchmark_core.py']:
        if sha(Path(__file__).with_name(name))!=meta['lemma_pipeline']['code'][name]:raise ValueError('Query/document code mismatch')
    if sha(root/'configs/model-installation.json')!=meta['lemma_pipeline']['model_installation']:raise ValueError('Query/document model mismatch')
    queries=read(args.queries)
    if not queries or len({q['query_id'] for q in queries})!=len(queries):raise ValueError('Empty or duplicate queries')
    if any(not q['query'].strip() for q in queries):raise ValueError('Empty query')
    args.output.mkdir(parents=True,exist_ok=False)
    annotations=FullTextLemmatizer(args.device).annotate([q['query'] for q in queries])
    pool={}
    with (args.output/'runs.jsonl').open('w') as out,(args.output/'queries.jsonl').open('w') as qo:
        for q,ann in zip(queries,annotations):
            qo.write(json.dumps(dict(q,annotation=ann),ensure_ascii=False)+'\n')
            for mode in ['baseline','enhanced']:
                body=query_body(q['query'],ann['shoshan_lemma'] if mode=='enhanced' else None,args.weight,args.depth,args.slop)
                started=time.monotonic(); response=request(args.url+'/'+args.index+'/_search','POST',body)
                if response.get('timed_out') or response['_shards']['failed']:raise RuntimeError('Incomplete search')
                hits=[]
                for rank,h in enumerate(response['hits']['hits'],1):
                    doc=h['_source']
                    hits.append(dict(doc,rank=rank,score=h['_score'],matched_queries=h.get('matched_queries',[])))
                    pool[q['query_id'],doc['doc_id']]={'query_id':q['query_id'],'query':q['query'],
                        'doc_id':doc['doc_id'],'ref':doc['ref'],'text':doc['exact'],'relevance':None}
                out.write(json.dumps({'query_id':q['query_id'],'query':q['query'],'mode':mode,'request':body,
                    'total':response['hits']['total']['value'],'seconds':time.monotonic()-started,'hits':hits},ensure_ascii=False)+'\n')
    # Deterministically scrambled, deduplicated pool without model/rank labels.
    with (args.output/'judgments.jsonl').open('w') as f:
        for key in sorted(pool,key=lambda k:hashlib.sha256(repr(k).encode()).hexdigest()):f.write(json.dumps(pool[key],ensure_ascii=False)+'\n')
    (args.output/'manifest.json').write_text(json.dumps({'index':args.index,'index_metadata':meta,'queries_sha256':sha(args.queries),
        'lemma_weight':args.weight,'slop':args.slop,'depth':args.depth,'device':args.device,'code_sha256':sha(Path(__file__)),
        'elasticsearch':request(args.url)['version'],'note':'No relevance scores until judgments are supplied. Queries may be synthetic smoke examples.'},indent=2)+'\n')
    print('Saved ranked runs and a blinded relevance-judgment pool to '+str(args.output))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',default='http://127.0.0.1:19200');p.add_argument('--index',required=True)
    sub=p.add_subparsers(dest='command',required=True)
    l=sub.add_parser('load');l.add_argument('--corpus',type=Path,required=True);l.add_argument('--lemmas',type=Path,required=True);l.add_argument('--allow-partial',action='store_true')
    c=sub.add_parser('compare');c.add_argument('--queries',type=Path,required=True);c.add_argument('--output',type=Path,required=True)
    c.add_argument('--device',choices=['mps','cpu'],default='mps');c.add_argument('--weight',type=float,default=1.);c.add_argument('--depth',type=int,default=50)
    c.add_argument('--slop',type=int,default=10,help='Shared phrase flexibility; 0 is strict, 10 matches normal frontend search')
    args=p.parse_args();check_destination(args.url,args.index)
    if args.command=='compare' and (args.weight<0 or not 1<=args.depth<=1000 or not 0<=args.slop<=50):p.error('Invalid weight/depth')
    try:
        request(args.url)  # Fail before loading large corpus/annotation files.
        (load if args.command=='load' else compare)(args)
    except ConnectionError as error:
        p.exit(2,str(error)+'\n')

if __name__=='__main__':main()
