# coding=utf-8

from bs4 import BeautifulSoup
from data_utilities.util import ToratEmetData
from data_utilities import util
import re


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

