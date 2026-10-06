"""Model-independent preprocessing and conservative prediction alignment."""
import unicodedata

POLICY = 'unpointed-v1'
PUNCTUATION = {'־': '-', '׃': ':', '׀': '|', '׳': "'", '״': '"',
               '‘': "'", '’': "'", '“': '"', '”': '"'}
BIDI = set('\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069')


def normalize(text, policy=POLICY):
    """Return model text and original-boundary -> model-boundary map.

    Only Hebrew combining marks are removed. Punctuation is replaced, never
    deleted into adjacent words. No spelling, prefix or suffix rewriting.
    """
    if policy not in (POLICY, 'raw-v1'):
        raise ValueError('Unknown preprocessing policy')
    out, boundaries, size = [], [0], 0
    for char in text:
        if policy == 'raw-v1':
            piece = char
        else:
            decomposition = unicodedata.normalize(
                'NFKD' if '\ufb1d' <= char <= '\ufb4f' else 'NFD', char)
            piece = ''.join(PUNCTUATION.get(c, c) for c in decomposition
                if c not in BIDI and not ('\u0590' <= c <= '\u05ff'
                                         and unicodedata.category(c).startswith('M')))
            # Preserve non-Hebrew accents and their original normalization.
            if not any('\u0590' <= c <= '\u05ff' for c in decomposition):
                piece = '' if char in BIDI else PUNCTUATION.get(char, char)
        out.append(piece)
        size += len(piece)
        boundaries.append(size)
    return ''.join(out), boundaries


def map_target(text, start, end, surface, policy=POLICY):
    if not 0 <= start < end <= len(text) or text[start:end] != surface:
        raise ValueError('Source target span mismatch')
    clean, boundaries = normalize(text, policy)
    a, b = boundaries[start], boundaries[end]
    if a == b or clean[a:b] != normalize(surface, policy)[0]:
        raise ValueError('Target did not survive preprocessing')
    return clean, a, b, boundaries


def label_key(lemma):
    if lemma is None or lemma.strip() in ('', '_', '[BLANK]', '[UNK]', '[PAD]', '[MASK]'):
        return None
    # Preserve raw output separately; no roots, synonyms or maleh/haser merging.
    return normalize(lemma)[0].strip() or None


def align_token(tokens, start, end):
    """Require one exact enclosing surface-token span; never find first spelling."""
    matches = [t for t in tokens if t['start'] == start and t['end'] == end]
    return (matches[0], None) if len(matches) == 1 else (None, 'unaligned_target')


def stanza_lemma(words):
    """Project a segmented token onto one lexical word, independently of gold.

    Keep all original components in the prediction record. For a split token,
    select its single open-class word; otherwise abstain. Do not concatenate
    affix lemmas into the lexical label or choose a component by gold agreement.
    """
    if len(words) == 1:
        return label_key(words[0].get('lemma')), 'single_word'
    lexical = [w for w in words if w.get('upos') in
               {'NOUN', 'PROPN', 'VERB', 'ADJ', 'ADV', 'NUM'}]
    if len(lexical) != 1:
        return None, 'ambiguous_morphological_components'
    return label_key(lexical[0].get('lemma')), 'single_lexical_component'


def require_token_budget(tokenizer, text, maximum):
    """Preflight using each actual model tokenizer, with special tokens included."""
    ids = tokenizer(text, add_special_tokens=True, truncation=False)['input_ids']
    if len(ids) > maximum:
        raise ValueError(f'context_too_long: {len(ids)} > {maximum}')
    return len(ids)
