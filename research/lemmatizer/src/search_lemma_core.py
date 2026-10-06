"""Full-text Shoshan inference with explicit offsets and bounded contexts."""
import re
from benchmark_core import normalize, label_key

# Retain internal quote marks in acronyms; punctuation/hyphens separate tokens.
TOKEN = re.compile(r'\w+(?:[\'\"]\w+)*', re.UNICODE)


def token_spans(text):
    return [{'form':m.group(), 'start':m.start(), 'end':m.end()} for m in TOKEN.finditer(text)]


def chunks(text, tokens, fits):
    """Nonoverlapping whole-token windows, never silently truncate a model input."""
    start=0
    while start<len(tokens):
        end=start+1
        a=tokens[start]['start']
        if not fits(text[a:tokens[start]['end']]):
            yield start,end,None
            start=end;continue
        while end<len(tokens) and fits(text[a:tokens[end]['end']]): end+=1
        yield start,end,(a,tokens[end-1]['end'])
        start=end


class FullTextLemmatizer:
    def __init__(self,device='mps'):
        # Sets offline/cache environment before loading models.
        from run_inference import MODELS
        from shoshan import Lemmatizer
        from shoshan.normalize import normalize_text
        from shoshan.text import normalize_with_offset_map
        import torch
        if device=='mps' and not torch.backends.mps.is_available():raise ValueError('MPS unavailable')
        self.model=Lemmatizer(MODELS/'shoshan/model',MODELS/'shoshan/bank',device=device,blank_function_words=False)
        self.normalize_text=normalize_text
        self.offset_map=normalize_with_offset_map
        self.torch=torch

    def annotate(self, texts, batch=16):
        docs=[];items=[];dest=[]
        for text in texts:
            clean,boundaries=normalize(text)
            tokens=token_spans(clean)
            # Map each surviving normalized character back to source character.
            owners=[]
            for i,(a,b) in enumerate(zip(boundaries,boundaries[1:])): owners.extend([i]*(b-a))
            for t in tokens:
                t.update(original_start=owners[t['start']],original_end=owners[t['end']-1]+1,
                         lemma=t['form'],raw_lemma=None,status='surface_fallback',reason='non_hebrew')
            doc={'text':clean,'tokens':tokens};docs.append(doc)
            fits=lambda s:len(self.model.enc.tok(self.normalize_text(s),truncation=False,verbose=False)['input_ids'])<=160
            for lo,hi,window in chunks(clean,tokens,fits):
                if window is None:
                    tokens[lo]['reason']='token_exceeds_context_budget';continue
                a,b=window; context=clean[a:b]
                normalized,offsets=self.offset_map(context)
                for t in tokens[lo:hi]:
                    if not re.search('[א-ת]',t['form']):continue
                    start=t['start']-a
                    expected=self.normalize_text(t['form'])
                    mapped=offsets.get(start)
                    if mapped is None or normalized[mapped:mapped+len(expected)]!=expected:
                        t['reason']='normalization_alignment_failure';continue
                    items.append({'form':t['form'],'sentence':context,'start':start})
                    dest.append(t); t['context_start']=a;t['context_end']=b
        with self.torch.inference_mode():
            results=self.model.lemmatize(items,batch=batch)
        if len(results)!=len(dest):raise ValueError('Prediction count mismatch')
        for t,r in zip(dest,results):
            lemma=label_key(r.get('lemma'))
            t.update(raw_lemma=r.get('lemma'),model_source=r.get('source'),score=r.get('score'),pos=r.get('pos'))
            # One indexed position per source token. Never expand multiword output.
            if lemma and len(lemma.split())==1:
                t.update(lemma=lemma,status='ok',reason=None)
            else:t['reason']='empty_or_multiword_lemma'
        for doc in docs:doc['shoshan_lemma']=' '.join(t['lemma'] for t in doc['tokens'])
        return docs
