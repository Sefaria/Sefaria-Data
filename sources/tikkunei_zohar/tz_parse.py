# from docx import Document
from bs4 import BeautifulSoup
from tz_base import *


class TzParser(object):
    def __init__(self, filename, volume, language="english", starting_tikkun=None, starting_daf=None):
        self.file = filename
        self.volume = volume

        self.doc_rep = None
        self.elem_cursor = None
        self.word_cursor = None
        self.language = language

        self.words = []
        self.lines = []
        self.paragraphs = []
        self.dapim = []
        self.tikkunim = []

        self.word = None
        self.line = None
        self.paragraph = None
        self.daf = starting_daf if starting_daf else None
        self.tikkun = starting_tikkun if starting_tikkun else None

        self.title = None

    def read_file(self):
        with open(self.file, 'r') as f:
            contents = f.read()
            self.doc_rep = self.get_document_representation(contents)
            self.parse_contents()

    def get_document_representation(self, contents):
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
        print(self.elem_cursor)
        if self.cursor_is_tikkun():
            self.process_tikkun()
        elif self.cursor_contains_words():
            self.word = self.get_next_word()
            while self.word:
                self.word = self.get_next_word()
            self.word_cursor = None


    def cursor_is_tikkun(self):
        pass

    def process_tikkun(self):
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


class HtmlTzParser(TzParser):
    def __init__(self, filename, volume, language="english", starting_tikkun=None, starting_daf=None):
        TzParser.__init__(self, filename, volume, language, starting_tikkun, starting_daf)

    def get_document_representation(self, contents):
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


    def get_next_word(self):
        return None
        # word = None
        # while not word:
        #     while not self.cursor.name:
        #         self.cursor = self.cursor.next_sibling
        #         if self.cursor is None:
        #             return None
        #     word = self.process_cursor()


parser = HtmlTzParser("vol1.html", 1)
parser.read_file()

