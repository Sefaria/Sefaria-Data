from docx import Document
from bs4 import BeautifulSoup
from tz_base import *
import re
import csv

import logging

class TzParser(object):
    PUNCTUATION = {
        # '‘': True,
        '.': True,
        ':': True
    }
    def __init__(self, filename, volume, language="english", starting_tikkun=None, starting_daf=None):
        self.file = filename
        self.volume = volume

        self.doc_rep = None
        self.elem_cursor = None
        self.processed_elem_cursor = None
        self.word_cursor = None
        self.language = language

        self.tikkun_number = count(0)
        self.paragraph_number = count(0)

        self.words = []
        self.phrases = []
        self.lines = []
        self.paragraphs = []
        self.dapim = []
        self.tikkunim = []
        self.quoted = []

        self.word = None
        self.phrase = None
        self.line = None
        self.paragraph = None
        self.daf = starting_daf if starting_daf else None
        self.tikkun = starting_tikkun if starting_tikkun else None
        self.append_to_previous = False
        # self.current_footnote_text = None
        self.current_footnote = None

        self.title = None

    def read_file(self):
        self.doc_rep = self.get_document_representation()
        self.parse_contents()

    def get_document_representation(self):
        """Returns abstracted representation of doc"""
        pass

    def parse_contents(self):
        """Parse the document"""
        self.title = self.get_title()
        self.elem_cursor = self.move_cursor()
        while self.elem_cursor:
            self.process_cursor()
            self.elem_cursor = self.move_cursor()

    def process_cursor(self):
        self.processed_elem_cursor = self.get_processed_elem()
        #print(self.processed_elem_cursor['class'])
        if self.cursor_is_daf():
            self.daf = self.get_daf()
        elif self.cursor_is_tikkun():
            self.tikkun = self.get_tikkun()
        elif self.cursor_is_paragraph():
            if self.tikkun:
                self.process_paragraph()
        elif self.cursor_contains_words():  # this is not used for HtmlParser
            self.process_words()
            # self.word = self.get_next_word()
            # while self.word:
            #     self.word = self.get_next_word()
            # self.word_cursor = None

    def create_new_paragraph(self):
        self.paragraph = Paragraph(self.tikkun, self.daf, next(self.paragraph_number))
        self.paragraphs.append(self.paragraph)
        self.tikkun.paragraphs.append(self.paragraph)
        self.daf.paragraphs.append(self.paragraph)
        self.line = self.paragraph.add_new_line()
        self.lines.append(self.line)
        self.append_to_previous = False

    def get_processed_elem(self):
        pass

    def cursor_is_daf(self):
        pass

    def get_daf(self):
        pass

    def cursor_is_tikkun(self):
        pass

    def get_tikkun(self):
        pass

    def cursor_is_paragraph(self):
        pass

    def process_paragraph(self):
        pass

    def cursor_contains_words(self):
        pass

    def get_next_word(self):
        """Processes the next word in the cursor element"""
        pass

    def move_cursor(self):
        pass

    def get_title(self):
        """get the title of the document"""
        pass


class DocsTzParser(TzParser):
    def __init__(self, filename, volume, language="english", starting_tikkun=None, starting_daf=None):
        TzParser.__init__(self, filename, volume, language, starting_tikkun, starting_daf)
        self.paragraph_index = 0
        self.parsing_footnote  = False

    def get_document_representation(self):
        return Document(self.file)

    def get_title(self):
        return self.file

    def move_cursor(self):
        if self.paragraph_index < len(self.doc_rep.paragraphs):
            cursor = self.doc_rep.paragraphs[self.paragraph_index]
            self.paragraph_index += 1
            # print(cursor.text)
            return cursor
        else:
            return None

    def get_processed_elem(self):
        return self.elem_cursor

    def cursor_is_daf(self):
        return re.match(r'\[[0-9]+[ab]\]', self.processed_elem_cursor.text) is not None

    def get_daf(self):
        daf = Daf(self.processed_elem_cursor.text)
        self.dapim.append(daf)
        return daf

    def cursor_is_tikkun(self):
        return re.match(r'^\[?Tiqun', self.processed_elem_cursor.text) is not None

    def get_tikkun(self):
        # print(self.processed_elem_cursor.text)
        tikkun = Tikkun(self.processed_elem_cursor.text, next(self.tikkun_number))
        for run in self.processed_elem_cursor.runs:
            if run.text == '' and run.element.style == 'EndnoteReference':
                tikkun.words.append(Word("[ENDNOTE_REFERENCE]", None, None, self.daf, tikkun, None))
            else:
                tikkun.words.append(Word(run.text, None, None, self.daf, tikkun, None))
        print([word.text for word in tikkun.words])
        return tikkun # TODO: handle tikkun footnotes

    def cursor_is_paragraph(self):
        return self.processed_elem_cursor.text.strip() == '' and self.processed_elem_cursor.style.name == 'Normal'

    def process_paragraph(self):
        if not self.paragraph or len(self.paragraph.words) > 0:
            self.create_new_paragraph()
    # def cursor_contains_words(self):
    #     if paragraph.text

    def cursor_contains_words(self):
        return True  # catchall????

    @staticmethod
    def get_formatting(run):
        if run.bold and run.italic:
            formatting = Formatting.BOLD_ITALICS
        elif run.bold:
            formatting = Formatting.BOLD
        elif run.italic:
            formatting = Formatting.ITALICS
        elif run.font.color.rgb is not None:
            formatting = Formatting.FADED
        else:
            formatting = None
        return formatting

    def process_words(self):
        for run in self.processed_elem_cursor.runs:
            if self.parsing_footnote:
                for char in run.text:
                    self.process_word(char, True, run)
            else:
                if len(run.text) > 0 and run.text[0] == ' ':
                    self.append_to_previous = False
                # if run.style == Normal??
                # for i, elem_word in enumerate(run.text.split(' ')):
                # else process footnote?
                # append to previous?????
                if not self.append_to_previous or len(self.line.phrases) == 0:  # new phrase for run
                    formatting = DocsTzParser.get_formatting(run)
                    self.phrase = self.line.add_new_phrase(formatting)
                    self.phrases.append(self.phrase)
                if self.current_footnote and self.phrase.formatting and not self.parsing_footnote:
                    self.current_footnote.anchor = self.phrase
                    self.phrase.footnotes.append(self.current_footnote)
                    self.current_footnote = None
                if run.text == ' ':
                    self.append_to_previous = False
                else:
                    for i, elem_word in enumerate(run.text.split(' ')):
                        if i > 0:
                            self.append_to_previous = False
                        if '{' in elem_word or '}' in elem_word or '\n' in elem_word or '‹' in elem_word or '›' in elem_word:
                            for char in elem_word:
                                self.process_word(char, True)
                        elif elem_word == '':
                            # parse w/ beautiful soup
                            pass
                        else:
                            self.process_word(elem_word)
                    # print(run.text)
                            if len(run.text) > 0 and run.text[-1] != ' ':
                                self.append_to_previous = True
                            else:
                                self.append_to_previous = False

    def process_word(self, word, char=False, run=None):
        if word == '{':
            self.parsing_footnote = True
            self.append_to_previous = False
            self.current_footnote = Footnote(FootnoteType.CITATION, None)
        elif word == '}':
            self.parsing_footnote = False
            self.append_to_previous = False
        elif word == '‹':
            self.parsing_footnote = True
            self.append_to_previous = False
            self.current_footnote = Footnote(FootnoteType.SYMBOL, None)  # TODO: Get specific type from BS
        elif word == '›':
            self.parsing_footnote = False
            if self.current_footnote:  # TODO: handle errors
                self.current_footnote.anchor = self.word
                self.word.footnotes.append(self.current_footnote)
                self.current_footnote = None
        elif word == '\n':
            self.line = self.paragraph.add_new_line()
            self.lines.append(self.line)
            self.append_to_previous = False

        else:
            if self.parsing_footnote:
                if char: #why
                    self.current_footnote.text += word
                    self.current_footnote.formatting = DocsTzParser.get_formatting(run) if run else \
                        self.current_footnote.formatting
            elif self.append_to_previous:
                if self.parsing_footnote:
                    self.current_footnote.text += word
                else:
                    self.word.add_to_word(word)
                # self.append_to_previous = False
            else:
                if self.parsing_footnote:
                    self.current_footnote.text += " "
                    self.current_footnote.text += word
                else:
                    self.word = self.phrase.add_new_word(word)
                    self.word.footnotes = []
                    self.words.append(self.word)
                if self.current_footnote and not self.parsing_footnote:
                    self.current_footnote.anchor = self.word
                    self.word.footnotes.append(self.current_footnote)
                    self.current_footnote = None
            #print(self.word.text)

class HtmlTzParser(TzParser):
    FOOTNOTES = {
        "CharOverride-1": True,
        "CharOverride-2": True,
        "CharOverride-3": True,
        "CharOverride-4": True,
        "CharOverride-5": True,
        "CharOverride-6": True,
        "CharOverride-7": True,
        "CharOverride-8": True,
        "CharOverride-10": True,
        "er": True,
        "stars": FootnoteType.STAR,
        "infinity": FootnoteType.INFINITY,
        "triangle": FootnoteType.TRIANGLE
    }

    FORMATTING_CLASSES = {
        "it-text": Formatting.ITALICS,
        "grey-text": Formatting.FADED,
        "bd-it-text": Formatting.BOLD_ITALICS,
        "bd": Formatting.BOLD
    }

    SIDENOTE_CLASSES = {
        "it-text---side-notes": Formatting.ITALICS,
        "bd-it-text---side-notes": Formatting.BOLD_ITALICS,
    }

    APPEND_TO_WORD = [
        "dot-italic",
        'dot-roman',
    ]

    def __init__(self, filename, volume, language="english", starting_tikkun=None, starting_daf=None):
        TzParser.__init__(self, filename, volume, language, starting_tikkun, starting_daf)
        self.continue_phrase = False

    def get_document_representation(self):
        with open(self.file, 'r') as file:
            contents = file.read()
            return BeautifulSoup(contents, 'html.parser')

    def get_title(self):
        return self.doc_rep.title.getText()

    def move_cursor(self):
        """Return the next element at the line level"""
        if not self.elem_cursor:
            if self.language == "english":
                cursor = self.doc_rep.find_all("div", class_="_idGenObjectStyleOverride-1")[0].contents[0]
                if cursor.name:
                    return cursor
        else:
            cursor = self.elem_cursor
        # augment
        cursor = cursor.next_sibling
        while cursor and not cursor.name:
            cursor = cursor.next_sibling
        return cursor

    def get_processed_elem(self):
        """returns the elem if it is not just a container, otherwise, return useful element"""
        if  "_idGenObjectLayout-1" in self.elem_cursor["class"]:
            return self.elem_cursor.div
        else:
            return self.elem_cursor

    def cursor_is_daf(self):
        return "daf" in self.processed_elem_cursor["class"]

    def get_daf(self):
        daf = Daf(self.processed_elem_cursor.p.text)
        self.dapim.append(daf)
        return daf

    def cursor_is_tikkun(self):
        return "chapter-number-title" in self.processed_elem_cursor["class"]

    def add_tikkun_word_to_list(self, elems, arr):
        for child in elems:
            if isinstance(child, str):
                arr.append(child)
            elif not any (x in child.get('class', ['CharOverride-1']) for x in ['CharOverride-1', 'er---chapter-number-title', 'CharOverride-16']):
                self.add_tikkun_word_to_list(child, arr)

    def get_tikkun(self):
        # TODO: further cleaning of tikkunim
        res = []
        self.add_tikkun_word_to_list(self.processed_elem_cursor.children, res)
        title = (''.join(res))
        tikkun = Tikkun(title, next(self.tikkun_number))
        for text in res:
            tikkun.words.append(Word(text, None, None, self.daf, tikkun, None))
        self.tikkunim.append(tikkun)
        return tikkun

    # def cursor_is_footnote(self):
    #     return self.processed_elem_cursor["class"] in ["books"]
    #
    # def get_footnotes(self):
    #     return self.processed_elem_cursor["class"] in ["books"]

    def cursor_is_paragraph(self):
        return self.processed_elem_cursor.name == 'p' and self.processed_elem_cursor['class']

    def process_words(self, elem, formatting):
        """Process words or partial words and add to existing or new Word"""
        if (not self.append_to_previous or elem[0].isspace()) and not self.continue_phrase:  # new phrase
            self.append_to_previous = False
            self.phrase = self.line.add_new_phrase(formatting)
            self.phrases.append(self.phrase)
        self.continue_phrase = False
        for i, elem_word in enumerate(elem.split()):
            if i == 0 and (self.append_to_previous or re.match(r'[?.\].,:!]+$', str(elem_word))):  # ending punctuation
                self.word.add_to_word(elem_word)
            elif re.match(r'[?.\[\].,:!]*‘[?.\[\].,:!]*$', str(elem_word)): # punctuation with backtaick
                if re.match(r'[?.\[\].,:!]*‘[?.\[\].,:!]*$', str(elem_word)) and len(self.paragraph.quoted_cursor) > 0:   # self.paragraph.inside_quotes:
                    self.word.add_to_word(elem_word)
                else:
                    self.word = self.phrase.add_new_word(elem_word)
                    self.word.footnotes = []
                    self.paragraph.add_to_quoted_if_in_quotes(self.word)
                    self.words.append(self.word)
                # elif self.line.inside_quotes:
                # else:
                #     self.word = self.phrase.add_new_word(elem_word)
                #     self.words.append(self.word)
                #     self.line.add_to_quoted_if_necessary(self.word)
            else:
                self.word = self.phrase.add_new_word(elem_word)
                self.word.footnotes = []
                self.words.append(self.word)
                self.paragraph.add_to_quoted_if_in_quotes(self.word)
            #self.line.add_to_quoted_if_necessary(self.word)
            if '‘' in elem_word or '’' in elem_word:
                if re.match(r'^[?./‘\[\].,:!]+[a-zA-Z0-9]+.*$', str(elem_word)):  # starts with ‘
                    self.paragraph.add_new_quoted()  # create a Quote()
                    self.paragraph.add_to_quoted_if_in_quotes(self.word)
                    if re.match(r'.*[?.\[\].,:!]*’[?.\[\].,:!]*', str(elem_word)):  # word ends in punctuation including ‘
                        self.paragraph.commit_quoted()
                    # number += 1
                    # if number != 1:
                    #    print("help!")
                    # self.line.add_new_quoted()
                elif re.match(r'^[a-zA-Z0-9]+[?.\[\].,:!]*’[?.\[\].,:!]*$', str(elem_word)):  # word ends in punctuation including backtick but doesn't start with
                    self.paragraph.commit_quoted()
                elif re.match(r'[A-Za-z]+’[A-Za-z]+', str(elem_word)):
                    pass
                else:  # just ‘
                    # if self.line.inside_quotes:
                    #     self.line.commit_quoted()
                    # else:
                    #     self.line.add_new_quoted()
                    #     self.line.add_to_quoted(self.word)
                    # pass
                    # print(word)
                    if '‘' in elem_word:  # new quoted
                        if elem_word != '‘':
                            print(elem_word)
                        self.paragraph.add_new_quoted()
                        self.paragraph.add_to_quoted_if_in_quotes(self.word)
                    else:
                        if self.file == 'vol2.html' and self.has_vol_1_exceptions(elem_word):
                            pass
                        else:
                            if len(self.paragraph.quoted_cursor) == 0: #assume typo? # need to fix this see "and who raises her to her place"
                                pass
                                # print(self.word.text)
                                # self.paragraph.add_new_quoted()
                                # self.paragraph.add_to_quoted_if_in_quotes(self.word)
                            else:
                                self.paragraph.commit_quoted()
                        # if len(self.paragraph.quoted_cursor) == 0:  # self.paragraph.inside_quotes:
                        #     print(elem_word)
                        #print(str(elem_word))

                # if it's start
                # if it's end
                # if it's both

        self.append_to_previous = not elem[-1].isspace()

    def has_vol_1_exceptions(self, elem_word):
        if len(self.paragraphs) == 33 and len(self.paragraph.words) == 24:  # specific exception for typo
            return True
        elif '-’A' in elem_word:
            return True
        elif elem_word == '’ezer':
            return True
        elif elem_word == 'te-ru’ah':
            return True
        else:
            return False

    def process_footnote_material(self, elem):
        pass

    def process_paragraph_elem(self, elem, paragraph, formatting=None):
        #try:
            if isinstance(elem, str):
                self.process_words(elem, formatting)
            elif elem.name == 'span' and 'id' in elem.attrs and 'endnote-'in elem['id']:
                # TODO: figure out where these endnotes are
                pass
            elif elem.name == 'span' and any(x in HtmlTzParser.FOOTNOTES for x in elem['class']):  # Footnotes
                #footnote_type = [x in elem['class'] if x in HtmlTzParser.FOOTNOTES]
                #self.word.add_new_footnote(elem)
                pass

            elif elem.name == 'span' and all(x not in HtmlTzParser.FOOTNOTES for x in elem['class']):  # Formatted text
                for child in elem.children:  # exception for gray-text override-9
                    if 'grey-text' in elem['class'] and 'CharOverride-9' in elem['class']:
                        format_class = None
                    else:
                        format_class = [x for x in elem['class'] if x in HtmlTzParser.FORMATTING_CLASSES][0] if \
                            any(x in HtmlTzParser.FORMATTING_CLASSES for x in elem['class']) else None
                    if len([x for x in elem['class'] if x in HtmlTzParser.APPEND_TO_WORD]) > 0:
                        self.continue_phrase = True
                    self.process_paragraph_elem(child, paragraph, format_class)
            elif elem.name == 'br':
                self.line = self.paragraph.add_new_line()
                self.lines.append(self.line)
                self.append_to_previous = False
            elif elem.name != 'img':
                raise Exception("Unhandled: " + str(elem))
                # TODO: handle unhandled
                pass
        #except Exception as e:
        #    logging.error("Error for parsing element " + str(elem) + ". " + str(e))
        # elif #citation
        #     pass
        # new line

    def process_paragraph(self):
        # print([a for a in self.processed_elem_cursor.children])
        self.create_new_paragraph()
        for child in self.processed_elem_cursor.children:
            self.process_paragraph_elem(child, self.paragraph)

    def get_next_word(self):
        return None

#
# parser2 = DocsTzParser("vol3.docx", 3)
# parser2.read_file()

# print(parser2.doc_rep)

# parser = HtmlTzParser("vol2.html", 1)
# parser.read_file()
# for line in parser2.lines:
#     print("---")
#     for phrase in line.phrases:
#         #if any(['‘' in word.text for word in phrase.words]):
#             print(phrase.formatting)
#             print([word.text for word in phrase.words])

    # for quoted in line.quoted:
    #     print([word.text for word in quoted.words])
# for phrase in parser.phrases:
#     print([word.text for word in phrase.words])
#
# if '‘' in word:
#     if re.match(r'^[?./‘\[\].,:!]+[a-zA-Z0-9]+.*$', str(word)):  # starts with ‘
#         self.line.add_new_quoted()  # create a Quote()
#         if re.match(r'[?.‘\[\].,:!]+$', str(word)):  #
#             self.line.commit_quoted()
#         number += 1
#         # if number != 1:
#         #    print("help!")
#         # self.line.add_new_quoted()
#     elif re.match(r'^[a-zA-Z0-9]+[?.‘\[\].,:!]+$', str(word)):  # or re.match('^[?.‘.:!]+'):
#         self.line.commit_quoted()
#         # self.line.commit_quoted()
#         # print('end quote')
#         # print(word)
#         number -= 1
#         # if number != 0:
#         #    print("help")
#     else:
#         if self.line.inside_quotes:
#             self.line.commit_quoted()
#         else:
#             self.line.add_new_quoted()
#         # pass
#         # print(word)
#     # if it's start
#     # if it's end
#     # if it's both


# parsers = [HtmlTzParser("vol2.html", 2), DocsTzParser("vol3.docx", 3), DocsTzParser("vol4.docx", 4), DocsTzParser("vol5.docx", 5)]
parsers = [DocsTzParser("vol4.docx", 4)]
for parser in parsers:
    parser.read_file()
    with open(f'tz_en_vol{parser.volume}.csv', 'w+') as tz_en:
        fieldnames = ["tikkun", "daf", "paragraph", "line", "phrase", "formatting", "footnotes"]
        csv_writer = csv.DictWriter(tz_en, fieldnames)
        csv_writer.writeheader()
        for phrase in parser.phrases:
            footnotes = []
            for word in phrase.words:
                for footnote in word.footnotes:
                    if type(footnote.anchor) is Word:
                        anchor = footnote.anchor.text
                    else: # Phrase
                        anchor = ' '.join([word.text for word in footnote.anchor.words])
                    footnotes.append(f"{footnote.footnote_type}/{footnote.formatting}[{anchor}]:{footnote.text}")
            for footnote in phrase.footnotes:
                anchor = ' '.join([word.text for word in footnote.anchor.words])
                footnotes.append(f"{footnote.footnote_type}/{footnote.formatting}[{anchor}]:{footnote.text}")
            row = {
                "tikkun": ' '.join([word.text for word in phrase.tikkun.words if word.text is not ' ']),
                "daf": phrase.daf.name,
                "paragraph": phrase.paragraph.paragraph_number,
                "line": phrase.line.line_number,
                "phrase": ' '.join([word.text for word in phrase.words]),
                "formatting": phrase.formatting,
                "footnotes": ';'.join(footnotes)
            }
            csv_writer.writerow(row)

    with open(f'tz_en_vol{parser.volume}_quotes.csv', "w+") as tz_en_quotes:
        fieldnames = ["tikkun", "daf", "paragraph", "line", "quotes", "formatting", "comments"]
        csv_writer = csv.DictWriter(tz_en_quotes, fieldnames)
