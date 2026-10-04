"""Pure text/span operations. No database access or Sefaria imports."""
import hashlib
import json
import re
import unicodedata
from html.parser import HTMLParser

PROCESSING_VERSION = 'plain-v1-skip-sup-footnotes'
MATCHING_VERSION = 'nfd-v2-quotes-maqaf'
MATCH_MODES = ('exact', 'cantillation_insensitive', 'vowel_insensitive',
               'exact_maqaf', 'cantillation_insensitive_maqaf', 'vowel_insensitive_maqaf')


def stable_id(kind, *parts):
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return kind + ':' + hashlib.sha256(raw.encode()).hexdigest()[:24]


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(attrs.get('class', '').split())
        hidden = tag in {'sup', 'script', 'style'} or bool(classes & {'footnote', 'footnote-marker'})
        if tag not in {'br', 'hr', 'img', 'input', 'meta', 'link', 'wbr'}:
            self.stack.append((tag, hidden or any(h for _, h in self.stack)))
        if not any(h for _, h in self.stack) and tag in {'br', 'p', 'div', 'li'}:
            self.parts.append(' ')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in {'br', 'hr', 'img', 'input', 'meta', 'link', 'wbr'}:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        if tag in {'p', 'div', 'li'} and not any(h for _, h in self.stack):
            self.parts.append(' ')

    def handle_data(self, data):
        if not any(h for _, h in self.stack):
            self.parts.append(data)


def plain_text(raw):
    parser = PlainText()
    parser.feed(raw)
    return re.sub(r'\s+', ' ', ''.join(parser.parts)).strip()


def ignored(char, mode):
    n = ord(char)
    if mode == 'cantillation_insensitive':
        return 0x591 <= n <= 0x5AF or n in {0x5BD, 0x5BF, 0x5C4, 0x5C5}
    if mode == 'vowel_insensitive':
        return 0x590 <= n <= 0x5FF and unicodedata.category(char).startswith('M')
    return False


def match_key(text, mode):
    """Map normalized characters back to complete original combining clusters."""
    maqaf = mode.endswith('_maqaf')
    if maqaf:
        mode = mode[:-6]
    chars, spans = [], []
    for match in re.finditer(r'.', text, flags=re.S):
        i = match.start()
        if unicodedata.combining(text[i]) and i:
            continue
        end = i + 1
        while end < len(text) and unicodedata.combining(text[end]):
            end += 1
        cluster = text[i:end]
        normalized = cluster if mode == 'exact' else unicodedata.normalize('NFD', cluster)
        for c in normalized:
            if not ignored(c, mode):
                chars.append(' ' if maqaf and c == '־' else c)
                spans.append((i, end))
    return ''.join(chars), spans


def word_character(c):
    return c.isalnum() or unicodedata.category(c).startswith('M')


def boundary_blocked(text, index, direction):
    if not 0 <= index < len(text):
        return False
    if word_character(text[index]):
        return True
    if text[index] in "׳״'\"":
        # A quote between letters belongs to a token (e.g. רש״י).
        other = index + direction
        return 0 <= other < len(text) and word_character(text[other])
    return False


def find_spans(text, form, mode):
    key, mapping = match_key(text, mode)
    needle, _ = match_key(form, mode)
    if not needle.strip():
        return []
    spans = set()
    pos = 0
    while True:
        start = key.find(needle, pos)
        if start < 0:
            break
        end = start + len(needle)
        pos = start + 1
        if boundary_blocked(key, start-1, -1):
            continue
        if boundary_blocked(key, end, 1):
            continue
        a, b = mapping[start][0], mapping[end-1][1]
        # A partial combining cluster must not count as an exact match.
        if match_key(text[a:b], mode)[0] == needle:
            spans.add((a, b))
    return sorted(spans)


def ranked_hebrew_versions(versions):
    """Primary Hebrew preferred; then same-language fallbacks for empty segments.

    Native version ordering is priority descending then _id ascending. Legacy
    language='he' alone is deliberately insufficient to admit a version.
    """
    def hebrew(v):
        family = v.get('languageFamilyName')
        return family.lower() == 'hebrew' if isinstance(family, str) and family else v.get('actualLanguage') == 'he'

    def priority(v):
        try:
            return float(v.get('priority') or 0)
        except (TypeError, ValueError):
            return 0.0

    eligible = sorted((v for v in versions if hebrew(v)), key=lambda v: (-priority(v), str(v['_id'])))
    primaries = [v for v in eligible if v.get('isPrimary') is True]
    preferred = primaries[0] if primaries else (eligible[0] if eligible else None)
    return ([preferred] + [v for v in eligible if v['_id'] != preferred['_id']]) if preferred else []
