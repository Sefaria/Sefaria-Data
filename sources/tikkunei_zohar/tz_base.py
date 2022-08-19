from enum import Enum
from itertools import count
from collections import OrderedDict

class Formatting(Enum):
    BOLD = 1
    ITALICS = 2
    BOLD_ITALICS = 3
    FADED = 4


class FootnoteType(Enum):
    CITATION = 1  # 2nd column
    SYMBOL = 2
    FOOTNOTE = 3
    INFINITY = 4
    STAR = 5
    TRIANGLE = 6


class Word(object):
    """Word in the Solomon Tikkunei Zohar"""
    ids = count(0)

    def __init__(self, text, phrase, line, paragraph, daf, tikkun, anchored_comments=[]):
        self.id = next(self.ids)
        self.text = text
        self.phrase = phrase
        self.line = line
        self.paragraph = paragraph
        self.daf = daf
        self.tikkun = tikkun
        self.anchored_comments = anchored_comments

    def add_to_word(self, str):
        self.text += str


class Phrase(object):
    """1 or more words or phrases formatted a particular way"""

    def __init__(self, formatting, line, paragraph, daf, tikkun):
        self.words = []
        self.line = line
        self.paragraph = paragraph
        self.daf = daf
        self.tikkun = tikkun
        self.formatting = formatting

    def add_new_word(self, text, anchored_comments=None):
        new_word = Word(text, self.line, self.paragraph, self.daf, self.tikkun, anchored_comments)
        self.words.append(new_word)
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

    def add_new_phrase(self, formatting):
        phrase = Phrase(formatting, self, self.paragraph, self.daf, self.tikkun)
        self.phrases.append(phrase)
        self.paragraph.phrases.append(phrase)
        self.daf.phrases.append(phrase)
        self.tikkun.phrases.append(phrase)
        return phrase

class Paragraph(object):
    """Multiple lines grouped together"""
    def __init__(self, tikkun, daf, paragraph_number):
        self.lines = []
        self.phrases = []
        self.tikkun = tikkun
        self.daf = daf
        self.paragraph_number = paragraph_number

    def add_new_line(self):
        line = Line(self, self.daf, self.tikkun)
        self.lines.append(line)
        self.tikkun.lines.append(line)
        self.daf.lines.append(line)
        return line


class Daf(object):
    def __init__(self, name):
        self.name = name
        self.lines = []
        self.paragraphs = []
        self.phrases = []


class Tikkun(object):
    def __init__(self, name, number):
        self.paragraphs = []
        self.lines = []
        self.phrases = []
        self.name = name
        self.number = number


class Footnote(object):
    def __init__(self, footnote, footnote_type, symbol, formatting, anchor=None):
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
