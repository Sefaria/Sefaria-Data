# coding=utf-8
from parsing_utilities.util import ToratEmetData
from parsing_utilities.util import ja_to_xml, multiple_replace
from bs4 import BeautifulSoup
import re
import unicodecsv as csv
import pdb
from fuzzywuzzy import fuzz
from sources import functions
from sefaria.model import *
from sefaria.utils.hebrew import hebrew_term

"""
parsed from this url: http://www.toratemetfreeware.com/online/f_01917.html
"""
url = 'http://www.toratemetfreeware.com/online/f_01917.html'


class PeneiDavid(ToratEmetData):

    def __init__(self, path, from_url=False, codec='cp1255'):

        ToratEmetData.__init__(self, path, from_url, codec)
        self.book_names = library.get_indexes_in_category('Torah')
        self.he_parsha_names = [re.sub(u'פרשת ', u'', x) for x in self._important_lines['parsha names']]
        self.parsha_names = []
        self.parsha_map = {}
        self.parsha_names_translated = {}
        self._build_parsha_map()
        self.parsha_by_book = self._get_parsha_by_book()
        self.parsed_as_dict = self._dict_parse()

    def _extract_important_data(self):

        book_names, parsha_names = [], []
        books, parashot, sections, segments = [], None, None, None

        def start_condition(html_fragment):

            soup = html_fragment
            if soup.u is not None:
                if soup.u.text == u'ספר בראשית':
                    return True
            return False

        def text_quote(html_fragment):
            soup = html_fragment
            if soup.div is None:
                return False
            else:
                return True

        def new_parsha(html_frament):
            soup = html_frament
            if soup.u is None:
                return False
            else:
                if re.search(u'פרשת ', soup.u.text):
                    return True
                else:
                    return False

        def new_book(html_frament):
            soup = html_frament
            if soup.u is None:
                return False
            else:
                if re.search(u'ספר', soup.u.text):
                    return True
                else:
                    return False

        text_started = False
        for line in self.lines:
            line = multiple_replace(line, {u'\n': u'', u'\r': u''})
            if re.match(u'<B', line) is None:
                continue

            soup = BeautifulSoup(line, 'html5lib')
            if text_started:
                if new_book(soup):
                    # add book name
                    book_names.append(soup.u.text)
                    if parashot is not None:
                        sections.append(segments)
                        parashot.append(sections)
                        books.append(parashot)

                    parashot, sections, segments = [], None, None

                elif new_parsha(soup):
                    parsha_names.append(soup.u.text)
                    if sections is not None:
                        sections.append(segments)
                        parashot.append(sections)

                    sections, segments = [], None

                    if text_quote(soup):
                        if segments is not None:
                            sections.append(segments)
                        segments = [soup.div.text]

                elif text_quote(soup):
                    if segments is not None:
                        sections.append(segments)
                    segments = [soup.div.text]

                else:
                    if soup.text == u'':
                        continue
                    else:
                        segments.append(soup.text)

            else:
                text_started = start_condition(soup)
                if text_started:
                    book_names.append(u'ספר בראשית')
                    parashot = []
        else:
            sections.append(segments)
            parashot.append(sections)
            books.append(parashot)
        return {
            'book names': book_names,
            'parsha names': parsha_names,
            'full_text': books
        }

    def _parse(self):
        return self._important_lines['full_text']

    def _build_parsha_map(self):
        with open('parsha.csv') as csvfile:

            he_to_en = {}

            reader = csv.reader(csvfile)
            for row in reader:

                # construct a dictionary mapping hebrew parsha names to english
                he_to_en[row[1]] = row[0]
                self.parsha_map[row[0]] = row[2]
                self.parsha_names_translated[row[0]] = row[1]

            for name in self.he_parsha_names:
                self.parsha_names.append(he_to_en[name])

    def _get_parsha_by_book(self):

        parsha_map = {}
        start = 0
        for book_num, book in enumerate(self._important_lines['full_text']):
            end = start + len(book)
            parsha_map[self.book_names[book_num]] = self.parsha_names[start:end]
            start = end
        return parsha_map

    def _dict_parse(self):

        books = {}
        for book_num, book in enumerate(self.parsed_text):
            book_name = self.book_names[book_num]
            parashot = {}

            for parsha_num, parsha in enumerate(book):
                parashot[self.parsha_by_book[book_name][parsha_num]] = parsha

            books[book_name] = parashot
        return books


def build_links(parser):
    """
    Use the PeneiDavid parsed text to generate links
    :param parser:
    :return:
    """

    assert isinstance(parser, PeneiDavid)
    links = []

    for book in parser.book_names:
        for parsha in parser.parsha_by_book[book]:
            parsha_ref = Ref(parser.parsha_map[parsha])
            print parsha_ref
            first_segment = Ref('{}.{}.{}'.format(book, *parsha_ref.sections))

            for sec_num, section in enumerate(parser.parsed_as_dict[book][parsha]):

                # verse is the first segment of each section
                best_match = None
                verse = re.sub(u'[^\u05d0-\u05ea ]', u'', section[0])
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

    assert isinstance(parser, PeneiDavid)

    root = SchemaNode()
    root.add_title('Penei David', 'en', primary=True)
    root.add_title(u'פני דוד', 'he', primary=True)
    root.key = 'Penei David'

    title_node = JaggedArrayNode()
    title_node.add_title('Title Page', 'en', primary=True)
    title_node.add_title(u'עמוד שער', 'he', primary=True)
    title_node.key = 'Title Page'
    title_node.depth = 1
    title_node.addressTypes = ['Integer']
    title_node.sectionNames = ["Paragraph"]
    root.append(title_node)

    # add book nodes
    for book in parser.book_names:
        book_node = SchemaNode()
        book_node.add_title(book, 'en', primary=True)
        book_node.add_title(hebrew_term(book), 'he', primary=True)
        book_node.key = book

        # add parsha nodes
        for parsha in parser.parsha_by_book[book]:
            parsha_node = JaggedArrayNode()
            parsha_node.add_title(parsha, 'en', primary=True)
            parsha_node.add_title(parser.parsha_names_translated[parsha], 'he', primary=True)
            parsha_node.key = parsha
            parsha_node.depth = 2
            parsha_node.addressTypes = ['Integer', 'Integer']
            parsha_node.sectionNames = ['Comment', 'Paragraph']
            book_node.append(parsha_node)

        root.append(book_node)
    root.validate()

    index = {
        "title": "Penei David",
        "categories": ["Commentary2", "Torah", "Penei David"],
        "schema": root.serialize()
    }
    return index


def upload_text(parser):

    assert isinstance(parser, PeneiDavid)
    for book in parser.book_names:
        for parsha in parser.parsha_by_book[book]:
            print 'uploading {}'.format(parsha)
            version = {
                "versionTitle": "Torat Emet Penei David",
                "versionSource": url,
                "language": 'he',
                "text": parser.parsed_as_dict[book][parsha]
            }
            functions.post_text("Penei David, {}, {}".format(book, parsha), version)

penei = PeneiDavid(url, True)
functions.post_index(build_index(penei))
upload_text(penei)
functions.post_link(build_links(penei))
