# from docx import Document
from bs4 import BeautifulSoup
from tz_base import *
from tz_base import Daf

class TzParser(object):
    def __init__(self, filename, volume, language="english", starting_tikkun=None, starting_daf=None):
        self.file = filename
        self.volume = volume

        self.doc_rep = None
        self.elem_cursor = None
        self.processed_elem_cursor = None
        self.word_cursor = None
        self.language = language
        self.tikkun_number = count(0)

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
        self.processed_elem_cursor = self.get_processed_elem()
        #print(self.processed_elem_cursor['class'])
        if self.cursor_is_daf():
            self.daf = self.get_daf()
        elif self.cursor_is_tikkun():
            self.tikkun = self.get_tikkun()
        elif self.cursor_contains_words():
            self.word = self.get_next_word()
            while self.word:
                self.word = self.get_next_word()
            self.word_cursor = None

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
        self.tikkunim.append(tikkun)
        return tikkun

    def get_next_word(self):
        return None

parser = HtmlTzParser("vol1.html", 1)
parser.read_file()

