# -*- coding: utf-8 -*-
'''
exceptions:
- footnotes: no [א] at כח:יז, no [א] at מ:כג / correct manually x
- small at יב:טז / manually make into footnote x
- לו has only one psuq, and it doesn't have the psuq in / correct x
- ב was terrible x

'''
import re
import os
import io
import sys
import pdb
import codecs
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

#path = u'/Users/joelbemis/Documents/programming/Sefaria-Data/sources/Malbim/Genesis/pages/'
#onePath = u'/Users/joelbemis/Documents/programming/Sefaria-Data/sources/Malbim/Genesis/perek 1/'

class Malbim(util.ToratEmetData):

    def __init__(self, path, from_url=False, codec='utf-8'):
        util.ToratEmetData.__init__(self, path, from_url, codec)
        self._important_lines = self._extract_important_data()
        self.parsed_text = self._parse()


    def _get_lines(self):
        pass

    @staticmethod
    def useless(html_fragment):
        soup = html_fragment
        if soup.text == u'' or soup.text == u'עריכה':
            return True
        return False


    @staticmethod
    def contains_chapter(html_fragment):
        soup = html_fragment
        if re.search(u'·', soup.text):
            return True
        return False


    @staticmethod
    def contains_verse(html_fragment):
        soup = html_fragment
        if re.match(u'\(([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2})\)', soup.text.strip()):
            return True
        return False


    @staticmethod
    def get_chapter(html_fragment):
        soup = html_fragment
        m = re.search(u'· ([\u05d0-\u05ea]{1,2}) ·', soup.text)
        return gematria(m.group(1))


    @staticmethod
    def get_verse(html_fragment):
        soup = html_fragment
        m = re.match(u'\(([\u05d0-\u05ea]{1,2})(\s?-?–?\s?)[\u05d0-\u05ea]{0,2}\)', soup.text.strip())
        return gematria(m.group(1))


    @staticmethod
    def is_question(html_fragment):
        soup = html_fragment
        if re.search('\xa0\xa0', soup.text) is not None:
            return True
        return False


    @staticmethod
    def is_footnote(html_fragment):
        soup = html_fragment
        if re.match(u'\[[\u05d0-\u05ea]\]', soup.text.strip()) is not None:
            return True
        return False


    @staticmethod
    def contains_DM(html_fragment):
        soup = html_fragment
        if soup.find('span', class_='psuq') is not None:
            return True
        return False


    @staticmethod
    def contains_range(html_fragment):
        soup = html_fragment
        if contains_range:
            return True
        return False


    @staticmethod
    def get_upper_range(html_fragment):
        soup = html_fragment
        m = re.match(u'\([\u05d0-\u05ea]{1,2}\s?-?–?\s?([\u05d0-\u05ea]{0,2})\)',chunk)
        return gematria(m.group(1))

    @staticmethod
    def contains_duplicates(commentaries):
        for c in commentaries:
            dupes = process.extract(c, commentaries)
            for d in dupes:
                if d[1] > 70:
                    return True
        return False


    def _extract_important_data(self):

        chapters, verses, text = {}, {}, []
        chapter, verse = 1, None

        for page in os.listdir(onePath):
            page = unicode(page)
            if page.startswith('.'):
                continue
            if verse and text:
                verses[verse] = text
                text = []
            verse = gematria(re.search(u'\u05d1\u05e8\u05d0\u05e9\u05d9\u05ea \u05d0 ([\u05d0-\u05ea]{1,2})', page).group(1))
            infile = io.open(onePath + page, 'r')
            soup = BeautifulSoup(infile, 'html5lib')
            infile.close()

            for p in soup.find_all('p'):
                if self.useless(p) or self.contains_chapter(p):
                    continue

                if self.is_question(p):
                    chunk = p.text.replace(u'\xa0\xa0', '').strip()
                    chunk = re.sub(u'\([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2}\)', u'<b>שאלות: </b>', chunk)
                    if chunk not in text:
                        text.append(chunk)
                elif self.is_footnote(p):
                    chunk = p.text.strip()
                    m = re.search(u'\[([\u05d0-\u05ea])\](.*)', chunk)
                    for segment in text:
                        if re.search(u'(\[' + m.group(1) + u'\])', segment):
                            i = text.index(segment)
                            text[i] = re.sub(u'(\[' + m.group(1) + u'\])', u'<sup>*</sup><i class="footnote">' + m.group(2) + u'</i>', text[i])
                else:
                    chunk = re.sub(u'\([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2}\)', u'', p.text.strip())
                    if self.contains_DM(p):
                        psuqim = p.find_all('span')
                        for psuq in psuqim:
                            chunk = re.sub(u'\"\s?' + psuq.text + u'\s?\"', ur'<strong>' + psuq.text + u'</strong>', chunk)
                    if chunk not in text:
                        text.append(chunk)

        verses[verse] = text
        text = []
        chapters[1] = verses
        verses = {}
        chapter = 2

        for page in os.listdir(path):
            print page
            cur_verse = 1
            if page.startswith('.'):
                continue
            infile = io.open(path+page , 'r')
            soup = BeautifulSoup(infile, 'html5lib')
            infile.close()


            for p in soup.find_all('p'):
                if self.useless(p):
                    continue

                if self.contains_chapter(p):
                    chapter = self.get_chapter(p)
                    continue

                if self.contains_verse(p):
                    new_verse = self.get_verse(p)
                    if cur_verse != new_verse and text:
                        verses[cur_verse] = text
                        text = []
                        cur_verse = new_verse

                if self.is_question(p):
                    chunk = p.text.replace(u'\xa0\xa0', '').strip()
                    chunk = re.sub(u'\([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2}\)', u'<b>שאלות: </b>', chunk)
                    if chunk not in text:
                        text.append(chunk)
                elif self.is_footnote(p):
                    chunk = p.text.strip()
                    m = re.search(u'\[([\u05d0-\u05ea])\](.*)', chunk)
                    for segment in text:
                        if re.search(u'(\[' + m.group(1) + u'\])', segment):
                            i = text.index(segment)
                            text[i] = re.sub(u'(\[' + m.group(1) + u'\])', u'<sup>*</sup><i class="footnote">' + m.group(2) + u'</i>', text[i])
                else:
                    chunk = re.sub(u'\([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2}\)', u'', p.text.strip())
                    if self.contains_DM(p):
                        psuqim = p.find_all('span')
                        for psuq in psuqim:
                            chunk = re.sub(u'\"\s?' + psuq.text + u'\s?\"', ur'<strong>' + psuq.text + u'</strong>', chunk)
                    if chunk not in text:
                        text.append(chunk)
            else:
                verses[cur_verse] = text
                text = []
                chapters[chapter] = verses
                verses = {}

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
                    malbim_ref = u'Malbim on Genesis {}:{}:1-{}'.format(unicode(chapter_index+1), unicode(verse_index+1), unicode(comment_len))
                else:
                    malbim_ref = u'Malbim on Genesis {}:{}:1'.format(unicode(chapter_index+1), unicode(verse_index+1))
                genesis_ref = u'Genesis {}:{}'.format(unicode(chapter_index+1), unicode(verse_index+1))
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
            "versionTitle": "Malbim on Genesis -- Wikisource",
            "versionSource": 'https://he.wikisource.org/wiki/%D7%9E%D7%9C%D7%91%D7%99%22%D7%9D_%D7%A2%D7%9C_%D7%91%D7%A8%D7%90%D7%A9%D7%99%D7%AA',
            "language": 'he',
            "text": book
        }
    functions.post_text("Malbim on Genesis", version, index_count='on')


malbim = Malbim(path)
#util.ja_to_xml(malbim.parsed_text, ['Chapter', 'Verse', 'Commentary'])
functions.post_index(build_index(malbim))
#upload_text(malbim)
#functions.post_link(build_links(malbim))
