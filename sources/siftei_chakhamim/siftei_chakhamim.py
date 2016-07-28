# encoding=utf-8
import codecs
from bs4 import BeautifulSoup
import urllib2
import re
from xml.etree import ElementTree as ET
import unicodecsv as ucsv
from data_utilities import util
from sefaria.model import *

"""
Very little data is available from the source file for this text. It is possible to break up text into chapters and
comments, but it isn't clear how to get from comments to the verses or Rashi comments. This data had to be "scraped"
from the web using the DaatRashiGrabber class, which attempts to match each comment to the correct verse and Rashi
comment.

It is important to note that the line breaks in this text are arbitrary, therefore it is necessary to treat the entire
text as one long string.

Chapters can be found using the @75-@73 pattern:
@75([\u05d0-\u05ea]{1,2})@73

Individual comments can be found with @55-@73, although work needs to be done to ensure there are no missed tags.
@55([\u05d0-\u05ea]{1,2})@73

This text numbers comments by letter (i.e. א,ב,ג...י,כ,ל). Therefore, a custom key is needed to examine the data.
"""

letters = {
    u'א': 1,
    u'ב': 2,
    u'ג': 3,
    u'ד': 4,
    u'ה': 5,
    u'ו': 6,
    u'ז': 7,
    u'ח': 8,
    u'ט': 9,
    u'י': 10,
    u'כ': 11,
    u'ל': 12,
    u'מ': 13,
    u'נ': 14,
    u'ס': 15,
    u'ע': 16,
    u'פ': 17,
    u'צ': 18,
    u'ק': 19,
    u'ר': 20,
    u'ש': 21,
    u'ת': 22,
}


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
            if span.text == u'\n':
                continue

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

    def add_to_xml(self, xml):
        """
        Adds derived data into an xml document
        :param xml: class ET.ElementTree
        """
        assert isinstance(xml, ET.ElementTree)

        # check if book node has been added
        root = xml.getroot()
        if root.find(self.book) is None:
            book = ET.SubElement(root, self.book)
        else:
            book = root.find(self.book)

        chapter = ET.SubElement(book, 'chapter', {'chap_index': str(self.chapter)})

        for rashi in self.rashis:
            verse = ET.SubElement(chapter, 'verse', {'verse_index': str(rashi['verse_number'])})

            for index, comment in enumerate(rashi['comments']):
                for super_comment in comment:
                    scomment = ET.SubElement(verse, 'comment', {'rashi_comment': str(index+1)})
                    scomment.text = super_comment

        return ET.ElementTree(root)
