'''
todo:
- if DM/range: generate reference for relevant psuqim (if multiple psuqim in commentary, should reference multiple psuqim)
- manually fix footnotes

exceptions:
- footnotes: no [א] at כח:יז, no [א] at מ:כג / correct manually
- small at יב:טז / manually make into footnote
- לו has only one psuq, and it doesn't have the psuq in / correct

'''
from data_utilities.util import ToratEmetData
from data_utilities.util import ja_to_xml, multiple_replace
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

path = '/pages'

class Malbim(ToratEmetData):

    def __init__(self, path, from_url=False, codec='cp1255'):
        ToratEmetData.__init__(self, path, from_url, codec)
        self.important_lines = self._extract_important_data()
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
    def get_location(html_fragment):
        soup = html_fragment
        if contains_verse(html_fragment):
            m = re.match(u'\(([\u05d0-\u05ea]{1,2})(\s?-?–?\s?)([\u05d0-\u05ea]{0,2})\)', soup.text)
            return gematria(m.group(1))
        else:
            return False


    @staticmethod
    def contains_verse(html_fragment):
        soup = html_fragment
        if re.match(u'\(([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2})\)', soup.text):
            return True
        return False


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

    @staticmethod
    def ranged_refs(html_fragment):
        soup = html_fragment
        m = re.match(u'\(([\u05d0-\u05ea]{1,2})(\s?-?–?\s?)([\u05d0-\u05ea]{0,2})\)', soup.text)
        if len(m.group(0)) > 4:
            return True
        return False



    def _extract_important_data(self):

        chapter, section, segments = None, {}, [],

        for page in os.listdir(self.path):

            cur_verse = 1
            infile = io.open('/pages/'+ page, 'r')
            soup = BeautifulSoup(infile, 'html5lib')
            infile.close()


            for p in soup.find_all('p'):
                if self.useless(p)
                    continue

                if self.contains_chapter(p):
                    m = re.search(u'· ([\u05d0-\u05ea]{1,2}) ·', p.text)
                    chapter = gematria(m.group(1))

                if self.contains_verse(p):
                    new_verse = get_location(p)

                if cur_verse != new_verse:
                    # what if section is empty
                    section['chapter'] = chapter
                    section['verse'] = cur_verse
                    if contains_duplicates(segments):
                        process.dedupe(segments)
                    section['text'] = segments
                    book.append(section)
                    section = {}
                    segments = []
                    cur_verse = new_verse

                if self.is_question(p):
                    chunk = p.text.replace(u'\xa0\xa0', '')
                    chunk = re.sub(u'\([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2}\)', u'<b>שאלות: </b>', chunk)
                    segments.append(chunk)
                elif self.is_footnote(p):
                    chunk = p.text
                    m = re.search(u'\[\u05d0\]', chunk)
                    segments[-1].replace(m.group(0), '<sup>*</sup><i class="footnote">' + chunk + '</i>')
                else:
                    chunk = p.text
                    if contains_DM(p):
                        m = p.find_all('span')
                        for psuq in m:
                            chunk = re.sub('\"' + psuq + '\"\.', 'B' + psuq + '\B', chunk)
                        chunk = re.sub(u'\"B(.*?)\B\"', r'<strong>\1</strong>', chunk)
                    if re.match(u'\([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2}\)',chunk):
                        m = re.match(u'\([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2}\)',chunk)
                        chunk.replace(m.group(0), '')
                    segments.append(chunk)

            section['chapter'] = chapter
            section['verse'] = cur_verse
            if contains_duplicates(segments):
                process.dedupe(segments)
            section['text'] = segments
            book.append(section)
            section = {}
            segments = []

        # is this correct:
        return book


    def _parse(self):
        return self._important_lines['full_text']


def build_links(parser):
    assert isinstance(parser, Malbim)
    links = []

    for perek in parser.book:
        for verse in perek:


    for book in parser.book_names:
        for parsha in parser.parsha_by_book[book]:
            parsha_ref = Ref(parser.parsha_map[parsha])
            print parsha_ref
            first_segment = Ref('{}.{}.{}'.format(book, *parsha_ref.sections))

            for sec_num, section in enumerate(parser.parsed_as_dict[book][parsha]):

                # verse is the first segment of each section
                best_match = None
                verse = re.sub
                segment = first_segment
                max_score = 0.0
                while parsha_ref.contains(segment):
                    sefaria_verse = segment.text('he', 'Tanach with Text Only').text
                    score = fuzz.partial_ratio(verse, sefaria_verse)
                    if score > max_score:
                        best_match = segment
                        max_score = score
                    segment = segment.next_segment_ref()
                    if segment is None:
                        break

                links.append({
                    'refs': [best_match.url(), 'Penei David, {}, {}.{}'.format(book, parsha, sec_num+1)],
                    'type': 'commentary',
                    'auto': False,
                    'generated_by': 'Penei David parse script'
                })

    return links


def build_index(parser):

    assert isinstance(parser, Malbim)

    root = SchemaNode()
    root.add_title(u'Malbim on Genesis', 'en', primary=True)
    root.add_title(u'מלבי״ם על בראשית', 'he', primary=True)
    # collective_title: u'Malbim'
    root.key = 'Malbim_on_Genesis'

        root.append(book_node)
    root.validate()

    index = {
        "title": "Malbim on Genesis",
        "categories": ["Commentary", "Torah", "Malbim"],
        "schema": root.serialize()
    }

    # add second index for Torah Or: See Trello
    index = {
        "title": "Torah Or",
        "categories": ["Commentary2", "Torah", "Torah Or"],
        "schema": root.serialize()
    }
    return index


def upload_text(parser):

    assert isinstance(parser, Malbim)
    for book in parser.book_names:
        for parsha in parser.parsha_by_book[book]:
            print 'uploading {}'.format(parsha)
            version = {
                "versionTitle": "",
                "versionSource": 'https://he.wikisource.org/wiki/%D7%9E%D7%9C%D7%91%D7%99%22%D7%9D_%D7%A2%D7%9C_%D7%91%D7%A8%D7%90%D7%A9%D7%99%D7%AA',
                "language": 'he',
                "text": parser.parsed_as_dict[book][parsha]
            }
            functions.post_text("Malbim, {}, {}".format(book, parsha), version)


malbim = Malbim(path)
functions.post_index(build_index(malbim))
upload_text(malbim)
functions.post_link(build_links(malbim))
