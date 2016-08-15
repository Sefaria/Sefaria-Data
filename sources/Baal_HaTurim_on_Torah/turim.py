# coding=utf-8

from bs4 import BeautifulSoup
from data_utilities.util import ToratEmetData
from data_utilities import util
import re
from sefaria.utils.hebrew import hebrew_term
from sources import functions
from sefaria.model import *


class TurimData(ToratEmetData):

    def _extract_important_data(self):
        def grab_chapter(html_fragment):
            he_chap = re.search(u'-([\u05d0-\u05ea]{1,2})-', html_fragment).group(1)
            return util.getGematria(he_chap)

        def grab_verse(html_fragment):
            he_verse = re.search(u'\{([\u05d0-\u05ea]{1,2})\}', html_fragment).group(1)
            return util.getGematria(he_verse)

        def clean(html_fragment):

            soup = BeautifulSoup(html_fragment, 'html.parser')
            soup.span.decompose()
            while soup.small is not None:
                soup.small.unwrap()
            for bold in soup.find_all(u'b'):
                if bold.text == u'':
                    bold.decompose()
            return unicode(soup)

        line_pattern = re.compile(u'<B><span')
        good_lines = []

        for line_number, line in enumerate(self.lines):
            if line_pattern.match(line):

                # data for chapter lies in the previous line
                chapter = grab_chapter(self.lines[line_number-1])
                verse = grab_verse(line)
                good_lines.append({
                    'chapter': chapter,
                    'verse': verse,
                    'text': clean(line)
                })
        return good_lines


def parse_multiple():

    turim = {}
    for book in library.get_indexes_in_category('Torah'):
        parser = TurimData('{}.html'.format(book))
        turim[book] = parser.parsed_text
    return turim


def linker(dict_of_ja):
    links = []

    for book in library.get_indexes_in_category('Torah'):
        for segment in util.traverse_ja(dict_of_ja[book]):

            refs = [u'{}.{}.{}'.format(book, *[x+1 for x in segment['indices'][:-1]]),
                    u'Baal HaTurim, {}.{}.{}.{}'.format(book, *[x+1 for x in segment['indices']])]

            links.append(
                {
                    'refs': refs,
                    'type': 'commentary',
                    'auto': False,
                    'generated_by': 'Baal HaTurim parse script'
                }
            )
    return links


def build_index():

    books = library.get_indexes_in_category('Torah')

    # create index record
    record = SchemaNode()
    record.add_title('Baal HaTurim', 'en', primary=True, )
    record.add_title(u'בעל הטורים', 'he', primary=True, )
    record.key = 'Baal HaTurim'

    # add nodes
    for book in books:
        node = JaggedArrayNode()
        node.add_title(book, 'en', primary=True)
        node.add_title(hebrew_term(book), 'he', primary=True)
        node.key = book
        node.depth = 3
        node.addressTypes = ['Integer', 'Integer', 'Integer']
        node.sectionNames = ['Chapter', 'Verse', 'Comment']
        node.toc_zoom = 2
        record.append(node)
    record.validate()

    index = {
        "title": "Baal HaTurim",
        "categories": ["Commentary2", "Torah", "Baal HaTurim"],
        "schema": record.serialize()
    }
    return index


def post_text(parsed_data):

    for book in library.get_indexes_in_category('Torah'):
        version = {
            'versionTitle': 'Baal HaTurim',
            'versionSource': 'http://www.toratemetfreeware.com/',
            'language': 'he',
            'text': parsed_data[book]
        }
        functions.post_text('Baal HaTurim, {}'.format(book), version)

parsed = parse_multiple()
links = linker(parsed)
index = build_index()
functions.post_index(index)
post_text(parsed)
functions.post_link(links)