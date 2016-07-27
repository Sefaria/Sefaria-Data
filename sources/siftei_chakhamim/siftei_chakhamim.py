# encoding=utf-8
import codecs
from bs4 import BeautifulSoup
import urllib2
import re
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

            for line in span.text.split(u'\n'):
                if line is not u'':
                    # add all Siftei Chakhamim in an array according to each Rashi comment.
                    verse['comments'].append(re.findall(u'\[([\u05d0-\u05ea])\]', line))

            rashis.append(verse)
        return rashis

    def write_to_csv(self, output_file):

        for rashi in self.rashis:
            for index, comment in enumerate(rashi['comments']):
                for super_comment in comment:
                    output_file.write(u'{};{};{};{};{}\n'.format(
                        self.book, self.chapter, rashi['verse_number'], index+1, super_comment
                    ))

