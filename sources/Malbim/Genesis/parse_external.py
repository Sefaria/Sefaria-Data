# -*- coding: utf-8 -*-
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

# path = '/Users/joelbemis/Documents/programming/Sefaria-Data/sources/Malbim/Genesis/external/commentary.txt'

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
                if self.contains_DM(chunk):
                    chunk = re.sub(u'@33(.*?)@44', ur'<b>\1</b>', chunk)
                text.append(chunk.strip())

        else:
            infile.close()

        return chapters


    def _parse(self):
        book = self._important_lines
        for chapter in book.keys():
            book[chapter] = util.convert_dict_to_array(book[chapter])
        book = util.convert_dict_to_array(book)
        return book


def build_links(parser):
    assert isinstance(parser, Malbim)
    book = parser.parsed_text
    links = []

    for chapter in book:
        chapter_index = book.index(chapter)
        for verse in chapter:
            verse_index = chapter.index(verse)
            if chapter[verse_index]:
                comment_len = len(chapter[verse_index])
                if comment_len > 1:
                    malbim_ref = 'Malbim on Genesis {}:{}:1-{}'.format(unicode(chapter_index+1), unicode(verse_index+1), unicode(comment_len))
                else:
                    malbim_ref = 'Malbim on Genesis {}:{}:1'.format(unicode(chapter_index+1), unicode(verse_index+1))
                genesis_ref = 'Genesis {}:{}'.format(unicode(chapter_index+1), unicode(verse_index+1))
                links.append({
                    'refs': [genesis_ref, malbim_ref],
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
        "collective_title": "Malbim",
        "base_text_titles": ["Genesis"],
        "categories": ["Tanakh", "Torah", "Commentary", "Malbim"],
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
    functions.post_text("Malbim on Genesis", version, index_count='on')


malbim = Malbim(path)
functions.post_index(build_index(malbim))
upload_text(malbim)
functions.post_link(build_links(malbim))
