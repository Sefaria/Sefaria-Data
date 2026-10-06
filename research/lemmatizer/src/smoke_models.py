"""Offline installation smoke test; not a benchmark or accuracy measurement."""
import argparse
import json
import os
import sys
from pathlib import Path
import time
from importlib.metadata import version

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT/'models'
os.environ['HF_HOME'] = str(MODELS/'hf_cache')
os.environ['HF_MODULES_CACHE'] = str(MODELS/'hf_modules')
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=['dicta', 'shoshan', 'stanza'], required=True)
    parser.add_argument('--device', choices=['cpu', 'mps'], default='cpu')
    args = parser.parse_args()
    import torch
    from transformers import AutoModel, AutoTokenizer
    if args.device == 'mps' and not torch.backends.mps.is_available():
        raise RuntimeError('Apple MPS is unavailable')
    sentence = 'הילדים קראו בספרים.'
    start = time.monotonic()
    config = json.loads((ROOT/'configs/comparison.json').read_text())
    if args.model == 'dicta':
        tokenizer = AutoTokenizer.from_pretrained(MODELS/'dicta', local_files_only=True)
        # Transformers' dynamic loader misses transitive sibling modules in this
        # snapshot. Import its unchanged pinned Python files together instead.
        sys.path.insert(0, str(MODELS/'dicta'))
        from BertForLexPrediction import BertForLexPrediction
        model = BertForLexPrediction.from_pretrained(
            MODELS/'dicta', local_files_only=True).to(args.device).eval()
        with torch.inference_mode():
            prediction = model.predict([sentence], tokenizer, use_lexicon=False)
        devices = sorted({str(p.device) for p in model.parameters()})
    elif args.model == 'shoshan':
        from shoshan import Lemmatizer
        model = Lemmatizer(MODELS/'shoshan/model', MODELS/'shoshan/bank',
                           device=args.device, blank_function_words=False)
        prediction = model.annotate(sentence)
        devices = sorted({str(p.device) for p in model.enc.parameters()})
    else:
        import stanza
        model = stanza.Pipeline('he', dir=str(MODELS/'stanza'),
            processors=config['stanza']['processors'], package=None,
            device=args.device, download_method=stanza.DownloadMethod.NONE)
        doc = model(sentence)
        prediction = [[{'form': t.text, 'start': t.start_char, 'end': t.end_char,
                        'words': [{'text': w.text, 'lemma': w.lemma, 'upos': w.upos}
                                  for w in t.words]} for t in s.tokens] for s in doc.sentences]
        devices = [str(model.device)]
    report = {'model': args.model, 'device': args.device, 'devices': devices,
        'mps_available': torch.backends.mps.is_available(), 'input': sentence,
        'prediction': prediction, 'elapsed_seconds': round(time.monotonic()-start,2),
        'versions': {n: version(n) for n in ['torch','transformers','stanza','shoshan']},
        'scope': 'installation smoke test only; no dataset evaluation'}
    out = ROOT/'datasets/model_installation'
    out.mkdir(parents=True, exist_ok=True)
    (out/f'{args.model}_{args.device}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
