# encoding=utf-8
import codecs
from bs4 import BeautifulSoup
import urllib2
import re
import unicodecsv as ucsv
from data_utilities import util
from sefaria.model import *


class DaatRashiGrabber:

    base_url = 'http://www.daat.ac.il/daat/olam_hatanah/mefaresh.asp?book={}&perek={}&mefaresh=siftey'
    book_list = library.get_indexes_in_category('Torah')

    def __init__(self, chapter_ref):

        self.book = chapter_ref.book
        self.chapter = chapter_ref.sections[0]
        self.url = self.base_url.format(self.book_list.index(self.book)+1, self.chapter)
        self.html = urllib2.urlopen(self.url).read()
        self.parsed_html = BeautifulSoup(self.html, 'html.parser')
        self.rashis = self.grab_rashis()

    def grab_rashis(self):

        rashis = []
        for span in self.parsed_html.find_all('span', id='katom'):
            verse = {'comments': []}

            # grab the verse number
            match = re.search(u'\(([\u05d0-\u05ea]{1,2})\)', span.text)

            if match is None:
                verse['verse_number'] = '<unknown>'

            else:
                verse['verse_number'] = util.getGematria(match.group(1))

            for line in self.structure_rashi(span.text):
                if line is not u'':
                    # add all Siftei Chakhamim in an array according to each Rashi comment.
                    verse['comments'].append(re.findall(u'\[([\u05d0-\u05ea])\]', line))

            rashis.append(verse)
        return rashis

    @staticmethod
    def structure_rashi(rashi_text):
        """
        take rashi on a verse and break it up into individual comments
        :param rashi_text: unicode without any html tags
        :return:
        """
        current, comments = None, []
        lines = rashi_text.split(u'\n')
        for line in lines:
            if line == u'':
                continue

            elif line.find(u'-') >= 0 or current is None:
                if current is not None:
                    comments.append(current)
                current = line

            else:
                current += line
        else:
            if current is not None and current is not u'':
                comments.append(current)

        return comments

    def write_to_csv(self, output_file, headers=False):

        columns = [u'Book', u'Chapter', u'Verse', u'Comment', u'Super Comment']
        writer = ucsv.DictWriter(output_file, fieldnames=columns, encoding='utf-8')
        if headers:
            writer.writeheader()

        for rashi in self.rashis:
            for index, comment in enumerate(rashi['comments']):
                for super_comment in comment:
                    writer.writerow({
                        u'Book': self.book,
                        u'Chapter': self.chapter,
                        u'Verse': rashi['verse_number'],
                        u'Comment': index+1,
                        u'Super Comment': super_comment
                    })



