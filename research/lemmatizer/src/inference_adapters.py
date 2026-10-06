"""Local model loading, shared context windows and offset-based predictions."""
import sys
import re
from functools import lru_cache
from benchmark_core import label_key, stanza_lemma


class AlignmentError(ValueError):
    pass


def common_window(text, start, end, fits):
    """Grow a shared window around the entire target, on whitespace boundaries.

    The caller checks BOTH model tokenizers, including Shoshan normalization.
    Never cut a target, prefix or punctuation-attached word to make it fit.
    """
    if fits(text):
        return 0, len(text)
    words = list(re.finditer(r'\S+', text))
    touched = [i for i,w in enumerate(words) if w.start() < end and w.end() > start]
    if not touched:
        raise AlignmentError('empty_target')
    left, right = touched[0], touched[-1]
    a, b = words[left].start(), words[right].end()
    if not fits(text[a:b]):
        raise AlignmentError('target_exceeds_context_budget')
    left_open = right_open = True
    while left_open or right_open:
        if left_open:
            if left > 0 and fits(text[words[left-1].start():words[right].end()]):
                left -= 1
            else:
                left_open = False
        if right_open:
            if right+1 < len(words) and fits(text[words[left].start():words[right+1].end()]):
                right += 1
            else:
                right_open = False
    return words[left].start(), words[right].end()


def dicta_tokens(encoded, tokenizer, predictions):
    """Reproduce upstream ## grouping with the SAME tokenizer's source offsets."""
    pieces = tokenizer.convert_ids_to_tokens(encoded['input_ids'])
    excluded = set(tokenizer.all_special_tokens) - {tokenizer.unk_token, tokenizer.mask_token}
    groups = []
    for piece, (a,b) in zip(pieces, encoded['offset_mapping']):
        if piece in excluded:
            continue
        if piece.startswith('##'):
            if not groups:
                raise AlignmentError('orphan_wordpiece')
            groups[-1]['form'] += piece[2:]
            groups[-1]['end'] = b
        else:
            groups.append({'form': piece, 'start': a, 'end': b})
    if len(groups) != len(predictions):
        raise AlignmentError('dicta_token_count_mismatch')
    for group, (form, lemma) in zip(groups, predictions):
        if group['form'] != form:
            raise AlignmentError('dicta_token_sequence_mismatch')
        group['lemma'] = lemma
    return groups


def exact_target(tokens, start, end):
    hits = [t for t in tokens if t['start'] == start and t['end'] == end]
    if len(hits) != 1:
        raise AlignmentError('unaligned_target')
    return hits[0]


class Adapter:
    def __init__(self, name, directory, config, device):
        import torch
        from transformers import AutoTokenizer
        self.name, self.torch = name, torch
        if name == 'dicta':
            self.tokenizer = AutoTokenizer.from_pretrained(directory/'dicta', local_files_only=True)
            sys.path.insert(0, str(directory/'dicta'))
            from BertForLexPrediction import BertForLexPrediction
            self.model = BertForLexPrediction.from_pretrained(
                directory/'dicta', local_files_only=True).to(device).eval()
        elif name == 'shoshan':
            from shoshan import Lemmatizer
            self.model = Lemmatizer(directory/'shoshan/model', directory/'shoshan/bank',
                                   device=device, blank_function_words=False)
        else:
            import stanza
            self.model = stanza.Pipeline('he', dir=str(directory/'stanza'),
                processors=config['stanza']['processors'], package=None,
                device=device, download_method=stanza.DownloadMethod.NONE)
        # Instance-owned cache avoids retaining past models through cached self keys.
        self.tokens = lru_cache(maxsize=16)(self._tokens)

    def _tokens(self, text):
        if self.name == 'dicta':
            encoded = self.tokenizer(text, truncation=False, return_offsets_mapping=True)
            if len(encoded['input_ids']) > 512:
                raise AlignmentError('context_too_long')
            with self.torch.inference_mode():
                prediction = self.model.predict([text], self.tokenizer, use_lexicon=False)[0]
            return dicta_tokens(encoded, self.tokenizer, prediction)
        doc = self.model(text)
        return [{'form': t.text, 'start': t.start_char, 'end': t.end_char,
                 'words': [{'text': w.text, 'lemma': w.lemma, 'upos': w.upos} for w in t.words]}
                for s in doc.sentences for t in s.tokens]

    def predict(self, text, start, end):
        if self.name == 'shoshan':
            from shoshan.normalize import normalize_text
            from shoshan.text import normalize_with_offset_map
            # Validate both length and normalized target location before the API,
            # which otherwise permits first-match/position-zero fallbacks.
            normalized, offsets = normalize_with_offset_map(text)
            form = text[start:end]
            mapped = offsets.get(start)
            expected = normalize_text(form)
            if mapped is None or normalized[mapped:mapped+len(expected)] != expected:
                raise AlignmentError('shoshan_normalized_target_mismatch')
            if len(self.model.enc.tok(normalized, truncation=False)['input_ids']) > 160:
                raise AlignmentError('context_too_long')
            encoded = self.model.enc.tok(normalized, truncation=False, return_offsets_mapping=True)
            spans = [(a,b) for a,b in encoded['offset_mapping'] if b > mapped and a < mapped+len(expected)]
            if not spans or min(a for a,b in spans) > mapped or max(b for a,b in spans) < mapped+len(expected):
                raise AlignmentError('shoshan_target_not_fully_encoded')
            with self.torch.inference_mode():
                raw = self.model.lemmatize([{'form':form,'sentence':text,'start':start}])[0]
            return {'raw_lemma':raw['lemma'], 'pred_cluster':label_key(raw['lemma']),
                    'projection':'explicit_target_span', 'details':raw}
        tokens = self.tokens(text)
        token = exact_target(tokens, start, end)
        if self.name == 'dicta':
            return {'raw_lemma':token['lemma'], 'pred_cluster':label_key(token['lemma']),
                    'projection':'wordpiece_offsets', 'details':token}
        lemma, method = stanza_lemma(token['words'])
        if method == 'ambiguous_morphological_components':
            return {'raw_lemma':None,'pred_cluster':None,'projection':method,'details':token,
                    'reason':method}
        selected = token['words'] if method == 'single_word' else [w for w in token['words']
            if w['upos'] in {'NOUN','PROPN','VERB','ADJ','ADV','NUM'}]
        return {'raw_lemma':selected[0]['lemma'], 'pred_cluster':lemma,
                'projection':method, 'details':token}
