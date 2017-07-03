'''
yoni questions:
- how to identify commentaries: (psuq ?- ?psuq) [except for ב]
- how to identify multiple commentaries: i.e. יא:ז
- how to deal with repeats?

shmuel quesitons:
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

        for filename in os.listdir(path):
            ToratEmetData.__init__(self, path + '/' + filename, from_url, codec)
            self.chapter = []
            self.verses = []
            self.parsed_as_dict = self._dict_parse()

    def _extract_important_data(self):

        book, chapters, verses, sections, segments = u'Genesis', [], [], [], [], None


        def new_chapter(html_fragment):

            soup = html_fragment
            if soup.h1 is not None:
                return True
            return False


        def new_verse(html_fragment):

            soup = html_fragment
            if soup.find('a', class_='mw-redirect', string=u'כל הפסוק') is not None:
                return True
            return False


        def new_question(html_fragment):

            if re.search('&#160;&#160;', html_fragment) is not None:
                return True
            return False


        def new_commentary(html_fragment):

            soup = html_fragment
            if soup.find() is not None:
                return True
            return False


        def new_DM(html_fragment):

            soup = html_fragment
            if soup.find('span', class_='psuq') is not None:
                return True
            return False


        def new_footnote(html_fragment):
            soup = html_fragment
            if soup.find('\[[ aleph - taf ]\]') is not None:
                return True
            return False

        text_started = False
        for line in self.lines:
            line = multiple_replace(line, {u'\n': u'', u'\r': u''})

            soup = BeautifulSoup(line, 'html5lib')
            if new_chapter(soup):
                chapters.append(gematria(soup.h1.text.strip().rsplit(' ', 1)[1]))

                if new_verse(soup):
                    tag = soup.find('a', class_='mw-redirect', string=u'כל הפסוק')
                    verses.append(gematria(tag.get('title').rsplit(' ', 1)[1]))

                elif new_question(soup):
                    # clean up text
                    sections.append('<b>שאלות: </b>' + soup.p.text)

                elif new_commentary(soup):
                    if pasuq(soup):

                    elif new_footnote(soup):

                    elif sections is not None:
                        sections.append(segments)
                        parashot.append(sections)

                    sections, segments = [], None

                        if text_quote(soup):
                            append('<b>' + soup.span.text + '</b>') # add quotation marks?
                            if segments is not None:
                                sections.append(segments)
                            segments = [NotImplemented] # soup.div.text

                else:
                    if soup.text == u'':
                        continue
                    else:
                        segments.append(NotImplemented) # soup.text

            else:
                text_started = start_condition(soup)

        else:
            sections.append(segments)
            parashot.append(sections)

        return {
            'book name': book_name
            'full_text': book
        }

    def _parse(self):
        return self._important_lines['full_text']


    def _dict_parse(self): # is this necessary?

        books = {}
        for book_num, book in enumerate(self.parsed_text):
            book_name = self.book_names[book_num]
            parashot = {}

            for parsha_num, parsha in enumerate(book):
                parashot[self.parsha_by_book[book_name][parsha_num]] = parsha

            books[book_name] = parashot
        return books


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
