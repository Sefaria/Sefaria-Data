'''
- repeats
- footnotes
- which verse for which chunk

s quesitons:
-
- how to deal with small at יב:טז
- how to deal with multiple psuqim in commentary i.e. טו:ה

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
from sefaria.model.text import library
from sefaria.datatype.jagged_array import JaggedArray
from sefaria.utils.hebrew import decode_hebrew_numeral as gematria
from sefaria.utils.hebrew import decompose_presentation_forms_in_str as normalize_he

path = '/pages'

class Malbim(ToratEmetData):

    def __init__(self, path, from_url=False, codec='cp1255'):
        ToratEmetData.__init__(self, path, from_url, codec)
        self.parsed_text = self._extract_important_data()


    def _extract_important_data(self):

        book, chapter, verse, sections, segments = {}, {}, {}, [], []


        def useless(html_fragment):

            soup = html_fragment
            if str(soup).find('<p><br/>') is 0 or soup.text == u'עריכה':
                return True
            return False


        def new_chapter(html_fragment):

            soup = html_fragment
            if str(soup).find(u'מלבי"ם על בראשית'):
                return True
            return False


        def new_verse(html_fragment):
            # check against verse
            soup = html_fragment
            if re.match(u'\(([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2})\)', html_fragment.text) is not None:
                return True
            return False


        def new_question(html_fragment):

            if re.search('<p><b>', html_fragment) is not None:
                return True
            return False


        def new_DM(html_fragment):

            soup = html_fragment
            if soup.find('span', class_='psuq') is not None:
                return True
            return False


        def new_footnote(html_fragment):
            soup = html_fragment
            if re.match(u'\[([\u05d0-\u05ea]{1,2})\]', soup.text) is not None:
                return True
            return False


        for page in listdir(self.path):

            first = True
            soup = BeautifulSoup(self.path + '/' + page, 'html5lib')
            psoup = soup.find_all('p')

            for p in psoup:
                if useless(p)
                    continue

                elif new_chapter(p):
                    m = re.search(u'· ([\u05d0-\u05ea]{1,2}) ·', p.text)
                    chapter = gematria(m.group(1))
                elif new_verse(p):
                    if not first:
                        line['chapter'] = chapter
                        line['verse'] = verse
                        line['text'] = sections
                        sections = []
                    else:
                        first = False
                    m = re.match(u'\(([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2})\)', p.text)
                    verse = gematria(m.group(1))
                    if new_DM(p):
                        pass
                    chunk = p.text
                    chunk = re.sub(u'<p>\([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2}\)(.*?)</p>', r'\1', chunk)
                    sections.append(chunk)
                elif new_question(p):
                    chunk = p.text
                    m = re.match(u'\(([\u05d0-\u05ea]{1,2})\s?-?–?\s?[\u05d0-\u05ea]{0,2}\)', chunk)
                    verse = m.group(1)
                    sections.append(re.sub(u'\([\u05d0-\u05ea]{1,2}\s?-?–?\s?[\u05d0-\u05ea]{0,2}\)', u'<b>שאלות: </b>', chunk))
                    # how to remove the &#160;
                elif new_footnote(p):
                    m = re.match(u'\[([\u05d0-\u05ea]{1,2})\]', p.text)
                    chunk = p.text
                    # not every footnote starts with [hebrew letter], but always an <h3> before it
                    # search last section item for m.group(0) [dif if plural] + replace with <sup>p.text</sup>
                    sections[-1].append('<sup>' + chunk '</sup>')
                else:
                    if new_DM(p):
                        pass
                    sections.append(p.text)


        book = convert_dict_to_array(book)

        return {
            'book name': book_name
            'full_text': book
        }

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
