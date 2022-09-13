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

    def __init__(self, text, phrase, line, paragraph, daf, tikkun, footnotes=[]):
        self.id = next(self.ids)
        self.text = text
        self.phrase = phrase
        self.line = line
        self.paragraph = paragraph
        self.daf = daf
        self.tikkun = tikkun
        self.footnotes = footnotes

    def add_to_word(self, str):
        self.text += str

    def add_new_footnote(self, footnote_type, formatting, footnote):
        footnote = Footnote(footnote_type, formatting, self, footnote)
        self.footnotes.append(footnote)
        return footnote

class Phrase(object):
    """1 or more words formatted a particular way"""

    def __init__(self, formatting, line, paragraph, daf, tikkun):
        self.words = []
        self.footnotes = []
        self.line = line
        self.paragraph = paragraph
        self.daf = daf
        self.tikkun = tikkun
        self.formatting = formatting

    def add_new_word(self, text, footnotes=None):
        new_word = Word(text, self.line, self.paragraph, self.daf, self.tikkun, footnotes)
        self.words.append(new_word)
        self.line.words.append(new_word)
        self.paragraph.words.append(new_word)
        return new_word

    def add_word_or_phrase(self, word_or_phrase):
        self.word_or_phrases.append(word_or_phrase)


class Quoted(object):
    def __init__(self, paragraph, daf, tikkun):
        self.words = []
        self.footnotes = []
        # self.line = line
        self.paragraph = paragraph
        self.daf = daf
        self.tikkun = tikkun
        self.complete = False

    def add_word(self, word):
        self.words.append(word)

    def end_quote(self):
        self.complete = True

    def is_complete(self):
        return self.complete

    def add_footnote(self, footnote):
        self.footnotes.append(footnote)


class Line(object):
    """Ordered phrases"""
    def __init__(self, paragraph, daf, tikkun):
        self.phrases = []
        self.paragraph = paragraph
        self.daf = daf
        self.words = []
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
        self.footnotes = []
        self.quoted = []
        self.words = []
        self.quoted_cursor = None
        self.inside_quotes = False
        self.enter_quotes_on_next_word = False
        self.exit_quotes_on_next_word = False
        self.tikkun = tikkun
        self.daf = daf
        self.paragraph_number = paragraph_number

    def add_new_line(self):
        line = Line(self, self.daf, self.tikkun)
        self.lines.append(line)
        self.tikkun.lines.append(line)
        self.daf.lines.append(line)
        return line

    def add_new_quoted(self):
        self.quoted_cursor = Quoted(self, self.daf, self.tikkun)
        self.inside_quotes = True
        # self.enter_quotes_on_next_word = True

    def commit_quoted(self):
        self.quoted.append(self.quoted_cursor)
        self.inside_quotes = False
        if self.quoted_cursor is None:
            print("End Quote Only")
        else:
            print([word.text for word in self.quoted_cursor.words])
        # self.exit_quotes_on_next_word = True

    def add_to_quoted_if_in_quotes(self, word):
        if self.inside_quotes:
            self.quoted_cursor.add_word(word)

    def add_to_quoted_if_necessary(self, word):
        if self.inside_quotes or self.enter_quotes_on_next_word:
            self.quoted_cursor.add_word(word)
            self.inside_quotes = True
            self.enter_quotes_on_next_word = False
        if self.exit_quotes_on_next_word:
            self.inside_quotes = False
            self.exit_quotes_on_next_word = False



class Daf(object):
    def __init__(self, name):
        self.name = name
        self.lines = []
        self.paragraphs = []
        self.phrases = []
        self.footnotes = []


class Tikkun(object):
    def __init__(self, name, number):
        self.paragraphs = []
        self.lines = []
        self.phrases = []
        self.footnotes = []
        self.name = name
        self.number = number


class Footnote(object):
    def __init__(self, footnote_type, formatting, anchor=None, footnote=None):
        self.anchor = anchor
        self.footnote = footnote
        self.footnote_type = footnote_type
        self.formatting = formatting


class TikkuneiZohar(object):
    def __init__(self):
        self.tikkunim = []
        self.dapim = []


# do we need the
