from enum import Enum
from itertools import count
from collections import OrderedDict


class Formatting(Enum):
    BOLD = 1
    ITALICS = 2
    FADED = 3


class FootnoteType(Enum):
    CITATION = 1  # 2nd column
    SYMBOL = 2
    FOOTNOTE = 3


class Word(object):
    """Word in the Solomon Tikkunei Zohar"""
    ids = count(0)

    def __init__(self, text, phrase, line, paragraph, daf, tikkun, anchored_comments):
        self.id = next(self.ids)
        self.text = text
        self.phrase = phrase
        self.line = line
        self.paragraph = paragraph
        self.daf = daf
        self.tikkun = tikkun
        self.anchored_comments = anchored_comments


class Phrase(object):
    """1 or more words or phrases formatted a particular way"""

    def __init__(self, formatting, line, paragraph, daf, tikkun):
        self.words_or_phrases = []
        self.line = line
        self.paragraph = paragraph
        self.daf = daf
        self.tikkun = tikkun
        self.formatting = formatting

    def add_new_word(self, text, anchored_comments):
        new_word = Word(text, self, self.line, self.paragraph, self.daf, self.tikkun, anchored_comments)
        self.words_or_phrases.append(new_word)
        return new_word

    def add_word_or_phrase(self, word_or_phrase):
        self.word_or_phrases.append(word_or_phrase)


class Line(object):
    """Ordered phrases"""
    def __init__(self, paragraph, daf, tikkun):
        self.phrases = []
        self.paragraph = paragraph
        self.daf = daf
        self.tikkun = tikkun

    def add_phrase(self, phrase):
        self.phrases.append(phrase)


class Paragraph(object):
    """Multiple lines grouped together"""
    def __init__(self, tikkun, daf):
        self.lines = []
        self.tikkun = tikkun
        self.page = daf

    def add_line(self, line):
        self.lines.append(line)


class Daf(object):
    def __init__(self, name):
        self.name = name
        self.lines = []
        self.paragraphs = []


class Tikkun(object):
    def __init__(self, name):
        self.paragraphs = []
        self.name = name


class Footnote(object):
    def __init__(self, anchor, footnote, footnote_type, symbol, formatting):
        self.anchor = anchor
        self.footnote = footnote
        self.footnote_type = footnote_type
        self.symbol = symbol
        self.formatting = formatting


class TikkuneiZohar(object):
    def __init__(self):
        self.tikkunim = []
        self.dapim = []


# do we need the
