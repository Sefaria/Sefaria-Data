from enum import Enum
from itertools import count
from collections import OrderedDict
from docx2python import docx2python

from sefaria.model import Ref


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
    ENDNOTE = 7
    DIAMONDS = 8  # second star


def get_symbol(footnote):
    if footnote.footnote_type == FootnoteType.INFINITY:
        return '∞'
    elif footnote.footnote_type == FootnoteType.STAR:
        return '☉'
    elif footnote.footnote_type == FootnoteType.DIAMONDS:
        return '☼'
    elif footnote.footnote_type == FootnoteType.TRIANGLE:
        return '△'
    elif footnote.footnote_type in [FootnoteType.FOOTNOTE, FootnoteType.ENDNOTE]:
        return footnote.footnote_number
    # elif footnote.footnote_type == FootnoteType.CITATION:
    #     # post citation
    #     return None
    else:
        return None


def get_tag(formatting_type, opening_tag=True):
    if not formatting_type:
        return ''
    attributes = None
    if formatting_type == Formatting.BOLD:
        tags = ['b']
    elif formatting_type == Formatting.FADED:
        tags = ['span']
        attributes = 'class="mediumGrey'
    elif formatting_type == Formatting.ITALICS:
        tags = ['i']
    elif formatting_type == Formatting.BOLD_ITALICS:
        tags = ['b', 'i']

    tag_string = ''
    for tag in tags:
        tag_string += f'<{"/" if not opening_tag else ""}{tag}{" " + attributes if attributes and opening_tag else ""}>'
    return tag_string


def strip_symbol(to_strip): # TODO: move into HtmlParser if HTML based
    for symbol in ['∞', '', '']:
        to_strip = to_strip.replace(symbol, '')
    return to_strip

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
        self.footnotes = []

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

    def add_new_word(self, text, footnotes=[]):
        new_word = Word(text, self.line, self.paragraph, self.daf, self.tikkun, footnotes)
        self.words.append(new_word)
        self.line.words.append(new_word)
        self.paragraph.words.append(new_word)
        # new_word.text)
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

    def __init__(self, paragraph, daf, tikkun, line_number):
        self.phrases = []
        self.paragraph = paragraph
        self.daf = daf
        self.words = []
        self.tikkun = tikkun
        self.line_number = line_number

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
        self.he_words = None
        self.quoted_cursor = []
        # self.inside_quotes = False
        self.enter_quotes_on_next_word = False
        self.exit_quotes_on_next_word = False
        self.tikkun = tikkun
        self.daf = daf
        self.paragraph_number = paragraph_number
        self.line_number = count(0)

    def add_new_line(self):
        line = Line(self, self.daf, self.tikkun, next(self.line_number))
        self.lines.append(line)
        self.tikkun.lines.append(line)
        self.daf.lines.append(line)
        return line

    def add_new_quoted(self):
        self.quoted_cursor.append(Quoted(self, self.daf, self.tikkun))
        # self.inside_quotes = True
        # self.enter_quotes_on_next_word = True

    def commit_quoted(self):
        if len(self.quoted_cursor) == 0:
            # print("End Quote Only")
            # print(self.words[-1].text)
            pass
        else:
            # print([word.text for word in self.quoted_cursor[-1].words])
            self.quoted.append(self.quoted_cursor[-1])
            # self.inside_quotes = False
            self.quoted_cursor.pop()

        # self.exit_quotes_on_next_word = True

    def add_to_quoted_if_in_quotes(self, word):
        # if len(self.quoted_cursor) > 0:
        for quote in self.quoted_cursor:
            quote.add_word(word)

    ref_replace_dict = {
        "Naḥ": "Nah",
        "Naḥ.": "Nah",
        "Ḥab": "Hab",
        "Lev.": "Lev",
        "Ez.": "Ezr",
        "1 King.": "1 Kings",
        "2 King.": "2 Kings",
        "Jer.": "Jeremiah",
        "Ez": "Ezra",
    }

    def get_links(self):
        links = []
        for footnote in self.footnotes:
            if footnote.footnote_type == FootnoteType.CITATION:
                ref1 = 'Tikkunei Zohar ' + self.daf.name + ':' + str(self.paragraph_number + 1)
                try:
                    for key, value in self.ref_replace_dict.items():
                        if footnote.text.startswith(key):
                            footnote.text = footnote.text.replace(key, value, 1)
                            footnote.text.replace('see: ', '')
                            footnote.text.replace('see ', '')
                            break
                    ref2 = Ref(footnote.text)
                    links.append({"refs": [ref1, str(ref2)], "type": "Citation", "auto": True, "generated_by": "solomon_tz_parse_nm"})
                except:
                    print('failed to parse ref ' + footnote.text)
        return links

    def get_words(self):
        words = ''
        for line in self.lines:
            for phrase in line.phrases:
                # for word in phrase.words:
                words_in_phrase = ''
                for word in phrase.words:
                    if words_in_phrase != '':
                        words_in_phrase += ' '
                    else:
                        words_in_phrase += get_tag(phrase.formatting)
                    words_in_phrase += word.text
                    for footnote in word.footnotes:
                        if type(footnote.anchor) is Word:
                            anchor = footnote.anchor.text
                        else:  # Phrase
                            anchor = ' '.join([word.text for word in footnote.anchor.words])
                        footnote_symbol = get_symbol(footnote)
                        if footnote_symbol:
                            words_in_phrase += '<sup class="footnote-marker">' + footnote_symbol + '</sup>' +\
                                               '<i class="footnote"><b>' \
                                               + '</b>' + strip_symbol(footnote.text) + '</i>'
                        else:
                            # TODO: handle other footnote types
                            pass
                words_in_phrase += get_tag(phrase.formatting, False)
                # words_in_phrase = ' '.join([word.text for word in phrase.words])
                if words != '':
                    words += ' '
                words += words_in_phrase
            words += '<br>'
        words.rstrip('<br>')
        # for footnote in phrase.footnotes:

        return words

    # def add_to_quoted_if_necessary(self, word):
    #     if self.inside_quotes or self.enter_quotes_on_next_word:
    #         self.quoted_cursor[-1].add_word(word)
    #         self.inside_quotes = True
    #         self.enter_quotes_on_next_word = False
    #     if self.exit_quotes_on_next_word:
    #         self.inside_quotes = False
    #         self.exit_quotes_on_next_word = False


class Daf(object):
    def __init__(self, name):
        self.name = name
        self.he_name = None
        self.lines = []
        self.paragraphs = []
        self.phrases = []
        self.footnotes = []
        self.paragraph_number = count(0)


class Tikkun(object):
    def __init__(self, name, number):
        self.words = []
        self.paragraphs = []
        self.he_name = None
        self.lines = []
        self.phrases = []
        self.footnotes = []
        self.name = name
        self.number = number


class Footnote(object):
    def __init__(self, footnote_type, formatting, anchor=None, text=''):
        self.anchor = anchor
        self.text = text
        self.footnote_type = footnote_type
        self.footnote_number = None
        self.formatting = formatting


class TikkuneiZohar(object):
    def __init__(self):
        self.tikkunim = []
        self.dapim = []

# do we need the
