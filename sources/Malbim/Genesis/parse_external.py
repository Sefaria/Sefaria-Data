# -*- coding: utf-8 -*-
'''
todo:
- fix parse

notes:
-concern: importing method will cause anything in the global scope to run,
 nesting the stuff in if '__name__ '== '__main__': prevents that from getting run
- gain access to Sefaria-Project with import sys / sys.path(append(path to Sefaria-Project))
 or could declare it as global variable in my os
*bad*
def foo(bar, spaz=[]):
    spaz.append(6)
    for i in spaz:
        print i

*good*
def foo(bar, spaz = none):
    if spaz is none:
        spaz = 6
    for i in spaz:
        print i

'''
import re
import os
import io
import sys
from bs4 import BeautifulSoup
from fuzzywuzzy import process
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from data_utilities import util
from sources.local_settings import *
from sources import functions
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedArray
from sefaria.utils.hebrew import decode_hebrew_numeral as gematria

path = '/Users/joelbemis/Documents/programming/Sefaria-Data/sources/Malbim/Genesis/external/commentary.txt'

class Malbim(util.ToratEmetData):

    def __init__(self, path, from_url=False, codec='utf-8'):
        util.ToratEmetData.__init__(self, path, from_url, codec)
        self._important_lines = self._extract_important_data()
        self.parsed_text = self._parse()

    @staticmethod
    def useless(html_fragment):
        soup = html_fragment
        if re.match(u'פרשת', soup):
            return True
        return False


    @staticmethod
    def contains_chapter(html_fragment):
        soup = html_fragment
        if re.match(u'@01פרק', soup):
            return True
        return False


    @staticmethod
    def contains_verse(html_fragment):
        soup = html_fragment
        if re.match(u'\{[\u05d0-\u05ea]{1,2}-?–?[\u05d0-\u05ea]{0,2}\}', soup) or re.match(u'@22', soup):
            return True
        return False


    @staticmethod
    def get_location(html_fragment):
        soup = html_fragment
        if re.search(u'\{([\u05d0-\u05ea]{1,2})-?–?[\u05d0-\u05ea]{0,2}\}', soup):
            m = re.search(u'\{([\u05d0-\u05ea]{1,2})-?–?[\u05d0-\u05ea]{0,2}\}', soup)
            return gematria(m.group(1))
        else:
            m = re.match(u'@01פרק\s(.{1,2})', soup)
            return gematria(m.group(1))


    @staticmethod
    def contains_question(html_fragment):
        if re.search(u'@22', html_fragment):
            return True
        return False


    @staticmethod
    def contains_DM(html_fragment):
        soup = html_fragment
        if re.search(u'@33', soup):
            return True
        return False


    def _extract_important_data(self):

        chapters, verses, text = {}, {}, []

        infile = io.open(path, 'r')
        cur_chapter = 41
        cur_verse = 1
        for line in infile:

            if self.useless(line):
                continue

            if self.contains_chapter(line):
                new_chapter = self.get_location(line)
                if new_chapter != cur_chapter:
                    verses[cur_verse] = text
                    text = []
                    chapters[cur_chapter] = verses
                    verses = {}
                    cur_chapter = new_chapter
                    cur_verse = 1
                continue

            if self.contains_verse(line):
                new_verse = self.get_location(line)
                if new_verse != cur_verse and text:
                    verses[cur_verse] = text
                    text = []
                    cur_verse = new_verse

            if self.contains_question(line):
                chunk = re.sub(u'@22\{[\u05d0-\u05ea]{1,2}-?–?[\u05d0-\u05ea]{0,2}\}', u'<b>שאלות: </b>',line)
                text.append(chunk.strip())
            else:
                chunk = re.sub(u'\{[\u05d0-\u05ea]{1,2}-?–?[\u05d0-\u05ea]{0,2}\}', u'',line)
                if self.contains_DM(line):
                    chunk = re.sub(u'@33(.*?)@44', ur'<b>\1</b>', chunk)
                text.append(chunk.strip())

        else:
            infile.close()

        return chapters


    def _parse(self):
        book = self._important_lines
        for chapter in book.keys():
            for verse in book[chapter].keys():
                book[chapter][verse] = util.convert_dict_to_array(book[chapter][verse])
            book[chapter] = util.convert_dict_to_array(book[chapter])
        book = util.convert_dict_to_array(book)
        return book



def build_links(parser):
    assert isinstance(parser, Malbim)
    book = parser._important_lines
    links = []

    for chapter in book.keys():
        for verse in chapter.keys():
            comment_len = str(len(chapter[verse]))
            malbim_ref = Ref('Malbim on Genesis' + chapter + ':' + verse + ":" + '1-' + comment_len)
            genesis_ref = Ref('Genesis' + chapter + ':' + verse)
            links.append({
                'refs': [malbim_ref, genesis_ref],
                'type': 'commentary',
                'auto': True,
                'generated_by': 'Malbim on Genesis external parse script'
            })
    return links


def build_index(parser):

    assert isinstance(parser, Malbim)

    schema = JaggedArrayNode()
    schema.add_primary_titles(u'Malbim on Genesis', u'מלבי״ם על בראשית')
    schema.add_structure(["Chapter", "Verse", "Comment"])
    schema.validate()

    index = {
        "title": "Malbim on Genesis",
        "categories": ["Torah", "Commentary", "Malbim"],
        "schema": schema.serialize()
    }

    return index


def upload_text(parser):

    assert isinstance(parser, Malbim)
    book = parser.parsed_text
    version = {
            "versionTitle": "Malbim, Vilna Romm, 1892.",
            "versionSource": 'http://dlib.rsl.ru/viewer/01006563898#?page=1',
            "language": 'he',
            "text": book
        }
    functions.post_text("Malbim on Genesis", version)


malbim = Malbim(path)
functions.post_index(build_index(malbim))
upload_text(malbim)
#functions.post_link(build_links(malbim))
