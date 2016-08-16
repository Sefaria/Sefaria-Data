# coding=utf-8
from data_utilities.util import ToratEmetData
from data_utilities.util import ja_to_xml, multiple_replace
from bs4 import BeautifulSoup
import re
import unicodecsv as csv
from sefaria.model import *

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

