'''
todo:
- waiting for last chapters with markers for DM?
- separate the two versions in the mean time upload the first part
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

exceptions:
- footnotes: no [א] at כח:יז, no [א] at מ:כג / correct manually x
- small at יב:טז / manually make into footnote x
- לו has only one psuq, and it doesn't have the psuq in / correct x
- ב was terrible x

'''
from data_utilities.util import ToratEmetData
import re
import os
import sys
import argparse
import unicodecsv
import local_settings
from bs4 import BeautifulSoup
from fuzzywuzzy import process
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedArray
from sefaria.utils.hebrew import decode_hebrew_numeral as gematria
from sefaria.utils.hebrew import decompose_presentation_forms_in_str as normalize_he

path = '/pages/'

class Malbim(ToratEmetData):

    def __init__(self, path, from_url=False, codec='cp1255'):
        ToratEmetData.__init__(self, path, from_url, codec)
        self._important_lines = self._extract_important_data()
        self.parsed_text = self._parse()


    @staticmethod
    def useless(html_fragment):
        soup = html_fragment
        if str(soup).find('<p><br/>') == 0 or soup.text == u'עריכה':
            return True
        return False


    @staticmethod
    def contains_chapter(html_fragment):
        soup = html_fragment
        if str(soup).find(u'מלבי"ם על בראשית'):
            return True
        return False


    @staticmethod
    def contains_verse(html_fragment):
        soup = html_fragment
        if re.match(u'\(([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2})\)', soup.text):
            return True
        return False


    @staticmethod
    def get_location(html_fragment):
        soup = html_fragment
        re.match(u'\(([\u05d0-\u05ea]{1,2})(\s?-?–?\s?)([\u05d0-\u05ea]{0,2})\)', soup.text):
        m = re.match(u'\(([\u05d0-\u05ea]{1,2})(\s?-?–?\s?)([\u05d0-\u05ea]{0,2})\)', soup.text)
        return gematria(m.group(1))

    @staticmethod
    def is_question(html_fragment):
        if re.search('<p><b>', html_fragment) is not None:
            return True
        return False


    @staticmethod
    def is_footnote(html_fragment):
        soup = html_fragment
        if re.match(u'\[\u05d0\]', soup.text) is not None:
            return True
        return False


    @staticmethod
    def contains_DM(html_fragment):
        soup = html_fragment
        if soup.find('span', class_='psuq') is not None:
            return True
        return False


    @staticmethod
    def contains_duplicates(commentaries):
        for c in commentaries:
            dupes = process.extract(c, commentaries)
            for d = dupes:
                if d[1] > 70:
                    return True
        return False


    def _extract_important_data(self):

        chapters, chapter, verses, text = [], 1, {}, []

        for page in os.listdir(self.path):

            cur_verse = 1
            infile = io.open(path + page, 'r')
            soup = BeautifulSoup(infile, 'html5lib')
            infile.close()


            for p in soup.find_all('p'):
                if self.useless(p)
                    continue

                if self.contains_chapter(p):
                    m = re.search(u'· ([\u05d0-\u05ea]{1,2}) ·', p.text)
                    chapter = gematria(m.group(1))
                    continue

                if self.contains_verse(p):
                    new_verse = self.get_location(p)
                    if cur_verse != new_verse and text:
                        if contains_duplicates(text):
                            process.dedupe(text)
                        verses[cur_verse] = text
                        text = []
                        cur_verse = new_verse

                if self.is_question(p):
                    chunk = p.text.replace(u'\xa0\xa0', '')
                    chunk = re.sub(u'\([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2}\)', u'<b>שאלות: </b>', chunk)
                    text.append(chunk.strip())
                elif self.is_footnote(p):
                    chunk = p.text.strip()
                    m = re.search(u'(\[[\u05d0-\u05ea]\])(.*?)', chunk)
                    for segment in text:
                        segment = re.sub(m.group(0), '<sup>*</sup><i class="footnote">' + m.group(1).strip() + '</i>', segment)
                else:
                    chunk = p.text
                    if self.contains_DM(p):
                        m = p.find_all('span')
                        for psuq in m:
                            chunk = re.sub('\"' + psuq + '\"\.', 'B' + psuq + '\B', chunk)
                        chunk = re.sub(u'\"B(.*?)\B\"', r'<strong>\1</strong>', chunk)
                    if re.match(u'\([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2}\)',chunk):
                        m = re.match(u'\([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2}\)',chunk)
                        chunk.replace(m.group(0), '')
                    text.append(chunk.strip())
            else:
                if contains_duplicates(text):
                    process.dedupe(text)
                verses[cur_verse] = text
                text = []
                chapters[chapter] = verses
                verses = {}

        return chapters


    def _parse(self):
        book = self._important_lines
        for chapter in book.keys():
            for verse in chapter.keys():
                chapter[verse] = convert_dict_to_array(chapter[verse])
            book[chapter] = convert_dict_to_array(book[chapter])
        book = convert_dict_to_array(book)
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
                'generated_by': 'Malbim on Genesis parse script'
            }
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
    book = parser.parsed_text:
    version = {
            "versionTitle": "Malbim on Genesis -- Wikisource",
            "versionSource": 'https://he.wikisource.org/wiki/%D7%9E%D7%9C%D7%91%D7%99%22%D7%9D_%D7%A2%D7%9C_%D7%91%D7%A8%D7%90%D7%A9%D7%99%D7%AA',
            "language": 'he',
            "text": book
        }
    functions.post_text("Malbim on Genesis", version)


malbim = Malbim(path)
#functions.post_index(build_index(malbim))
#upload_text(malbim)
#functions.post_link(build_links(malbim))
