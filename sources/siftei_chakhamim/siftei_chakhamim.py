# encoding=utf-8
import codecs
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET
import csv
import urllib2
import re
from data_utilities import util
import unicodecsv as ucsv
from data_utilities import util
from sefaria.utils.hebrew import hebrew_term
from sefaria.model import *
import json
from sources import functions

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
A sequence of characters and numbers can appear after the @55, so this must be accounted for.
@55(>!05#[0-9]{4}<)?([\u05d0-\u05ea]{1,2})@73

This text numbers comments by letter (i.e. א,ב,ג...י,כ,ל). Therefore, a custom key is needed to examine the data.

Missing data in the Genuzot source files led me to attempt a parse HTML taken from Torat Emet. This HTML does not have
a well formed tree like structure. The approach I took was to combine iterating line by line with the along with the
BeautifulSoup HTML parser.
"""

letters = {
    u'א': 0,
    u'ב': 1,
    u'ג': 2,
    u'ד': 3,
    u'ה': 4,
    u'ו': 5,
    u'ז': 6,
    u'ח': 7,
    u'ט': 8,
    u'י': 9,
    u'כ': 10,
    u'ל': 11,
    u'מ': 12,
    u'נ': 13,
    u'ס': 14,
    u'ע': 15,
    u'פ': 16,
    u'צ': 17,
    u'ק': 18,
    u'ר': 19,
    u'ש': 20,
    u'ת': 21,
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

            structured_rashi = self.structure_rashi(span.text)
            for line in structured_rashi:
                if line is not u'':
                    # add all Siftei Hakhamim in an array according to each Rashi comment.
                    verse['comments'].append(re.findall(u'\[([\u05d0-\u05ea])\]', line))

            verse['total_rashis'] = len(structured_rashi)

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

            elif re.search(u'-|\u2013', line) or current is None:
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
            total_rashis = ET.SubElement(verse, 'total_rashis')
            total_rashis.text = str(rashi['total_rashis'])

        return ET.ElementTree(root)


class TextParser:
    chap_reg = re.compile(u'@75([\u05d0-\u05ea]{1,2})@73')
    comment_reg = re.compile(u'@55(>!05#[0-9]{4}<)?([\u05d0-\u05ea]{1,2})@73')

    def __init__(self, file_name):
        self.file_name = file_name
        self.string = self.file_to_string()
        self.chapter_strings = self.string_to_chapters()
        self.parsed_chapters = self.parse_chapters()
        self.books = self.break_into_books()

    def file_to_string(self):
        with codecs.open(self.file_name, 'r', 'utf-8') as text_file:
            lines = [line.replace(u'\n', u'') for line in text_file]

        all_text = u' '.join(lines)
        all_text = re.sub(u' +', u' ', all_text)
        return all_text

    def string_to_chapters(self):

        # find all chapters
        matches = self.chap_reg.finditer(self.string)

        chapters = []
        start_index = next(matches)
        for next_index in matches:
            chapters.append(self.string[start_index.start():next_index.start()])
            start_index = next_index
        else:
            chapters.append(self.string[start_index.start():])

        return chapters

    def parse_chapters(self):
        chapters = []

        for unparsed in self.chapter_strings:
            matches = self.comment_reg.finditer(unparsed)
            comments = []
            start_index = next(matches)
            for next_index in matches:
                comments.append(unparsed[start_index.start():next_index.start()])
                start_index = next_index
            else:
                comments.append(unparsed[start_index.start():])
            chapters.append(comments)

        return chapters

    def break_into_books(self):

        books = []
        start = 0
        torah = library.get_indexes_in_category('Torah')
        for book in torah:
            end = start + len(Ref(book).all_subrefs())
            books.append(self.parsed_chapters[start:end])
            start = end

        return books


def recover_data(chapter):
    """
    Some of the verses do not have their verse index recorded on the daat site. Attempt to derive the missing data
    by examining the surrounding verses
    :param chapter: A 'class' Element from Elementtree of a single chapter
    """
    assert isinstance(chapter, ET.Element)

    # get all verse elements
    verses = chapter.findall("./verse")

    for index, verse in enumerate(verses):

        if verse.attrib['verse_index'] == '<unknown>':
            # is this the first verse?
            if index == 0:
                if verses[1].attrib['verse_index'] == '2':
                    verse.attrib['verse_index'] = '1'
            else:
                try:
                    previous = int(verses[index-1].attrib['verse_index'])
                    next_one = int(verses[index+1].attrib['verse_index'])
                except IndexError:
                    break
                except ValueError:
                    continue
                if next_one - previous == 2:
                    value = previous + 1
                    verse.attrib['verse_index'] = str(value)


def modulo_sequence(values, modulo, offset=0):
    """
    checks if values are sequential when values follow a modulo pattern (i.e. 0,1,2,3,0,1,2,3,0...)
    :param values: list of values to examine. Values must be zero indexed.
    :param modulo: number to run modulo on. In the example of 0,1,2,3 this would be 4
    :param offset: integer that can be used if values don't start at 0
    :return: Dictionary, with key in_order with a boolean value, and key errors a list of dictionaries
    with previous, expected and found.
    """
    errors = []

    for index, value in enumerate(values):
        expected = (index+offset) % modulo
        if expected != value:
            if index == 0:
                previous = None
            else:
                previous = values[index-1]
            errors.append({'previous': previous, 'expected': expected, 'found': value})

            # update offset to account for the skip
            offset += value - expected

    if len(errors) == 0:
        return {'in_order': True, 'errors': errors}
    else:
        return {'in_order': False, 'errors': errors}


def find_skips(filename):
    """
    Looks for skipped comments.
    :param filename: File to scan
    """

    parser = TextParser(filename)
    offset = 0
    total_errors = 0
    for chapter in parser.chapter_strings:
        chap_number = util.getGematria(parser.chap_reg.search(chapter).group(1))
        if chap_number == 1:
            offset = 0
        comments = parser.comment_reg.findall(chapter)
        comment_values = [letters[comment[1]] for comment in comments]

        sequence = modulo_sequence(comment_values, 22, offset)
        offset = comment_values[-1]+1

        if sequence['in_order']:
            continue
        else:
            print 'error in chapter {}'.format(chap_number)
            for error in sequence['errors']:
                print 'previous: {} expected: {} found: {}'.format(
                    error['previous'], error['expected'], error['found'])
            total_errors += len(sequence['errors'])
    print 'total errors: {}'.format(total_errors)


class HTMLParser:

    def __init__(self, filename, codec='cp1255'):
        self.filename = filename
        self.lines = self.file_by_lines(codec)
        self.important_text = self.important_lines()
        self.parsed_text = self.build_structure()

    def file_by_lines(self, codec):
        with codecs.open(self.filename, 'r', codec) as datafile:
            data = datafile.readlines()
        return data

    def important_lines(self):
        good_lines = []
        for line_num, line in enumerate(self.lines):
            if re.search(u'<B><span', line):
                data = {'text': self.remove_bad_tags(line)}

                # extract meatadata from previous line in file
                info = self.chapter_verse(self.lines[line_num-1])
                data['chapter'] = info['chapter']
                data['verse'] = info['verse']
                good_lines.append(data)

        return good_lines

    @staticmethod
    def remove_bad_tags(html_fragment):
        soup = BeautifulSoup(html_fragment, 'html.parser')
        while soup.small is not None:
            soup.small.unwrap()
        soup.span.decompose()
        for bold in soup.find_all('b'):
            if bold.text == u'':
                bold.decompose()
        return unicode(soup)

    @staticmethod
    def chapter_verse(text_fragment):
        searcher = re.compile(u'.*B.*-([\u05d0-\u05ea]{1,2})-\{([\u05d0-\u05ea]{1,2})\}')
        data = searcher.search(text_fragment)
        return {'chapter': util.getGematria(data.group(1)), 'verse': util.getGematria(data.group(2))}

    def build_structure(self):

        book = {}
        for line in self.important_text:
            chapter, verse = line['chapter'], line['verse']

            if chapter not in book.keys():
                book[chapter] ={}

            book[chapter][verse] = self.structure_comments(line['text'])

        book = util.convert_dict_to_array(book)
        for index, section in enumerate(book):
            book[index] = util.convert_dict_to_array(section)
        return book

    @staticmethod
    def structure_comments(text_fragment):

        comments = []

        bold = re.compile(u'<b>')
        matches = bold.finditer(text_fragment)
        start = next(matches)

        for next_match in matches:
            comments.append(text_fragment[start.start(): next_match.start()])
            start = next_match
        else:
            comments.append(text_fragment[start.start():])
        return comments


def parse_multiple():
    book_names = library.get_indexes_in_category('Torah')
    parsed_text = {}
    for book in book_names:
        parser = HTMLParser('{}.html'.format(book))
        parsed_text[book] = parser.parsed_text

    return parsed_text


def compare_data(parsed, daat_xml):
    """
    compare number of Rashi comments in our system to daat, as well as number of Siftei Hakhamim comments on Torat
    emet to daat.
    :param parsed: Parsed text as a dictionary, with book names as keys and ja as values.
    :param daat_xml: Filename of daat xml data
    :return:
    """
    daat = ET.parse(daat_xml)
    root = daat.getroot()
    comment_verses, bad_verses = 0, 0

    for book in library.get_indexes_in_category('Torah'):
        daat_book = root.find(book)
        daat_chapters = list(daat_book)
        for chap_index, chapter in enumerate(parsed[book]):
            # daat_verses = list(daat_chapters[chap_index])
            for v_index, verse in enumerate(chapter):

                bad_verse = False
                total_rashis = len(Ref('Rashi on {}.{}.{}'.format(book, chap_index+1, v_index+1)).all_subrefs())
                daat_verse = daat_chapters[chap_index].find("./verse[@verse_index='{}']".format(v_index+1))
                if daat_verse is None:
                    total_daat_comments = 0
                else:
                    total_daat_comments = len(daat_verse.findall("./comment"))
                    comment_verses += 1

                if total_daat_comments > 0:
                    total_daat_rashis = int(daat_verse.find("./total_rashis").text)
                else:
                    total_daat_rashis = 0

                if total_rashis != total_daat_rashis and len(verse) > 0:
                    print 'Rashi mismatch {} {} {}'.format(book, chap_index+1, v_index+1)
                    bad_verse = True

                if total_daat_comments != len(verse):
                    print 'comment mismatch {} {} {}'.format(book, chap_index+1, v_index+1)
                    bad_verse = True
                if bad_verse:
                    bad_verses += 1
    print 'verses with comments: {}\nbad verses: {}'.format(comment_verses, bad_verses)


def generate_links(parsed_data, link_filename='fixed_links.xml', error_file='errors.csv'):
    """
    Using an xml of data from daat and parsed text, generate all links
    :param parsed_data: Dictionary keys are books of Torah, values are parsed text into ja.
    :param link_filename: Filename of xml file that holds link data.
    :param error_file: Filename of csv file which contains all comments that could not be linked.
    :return: List of link objects
    """
    links, errors = [], []
    root = ET.parse(link_filename).getroot()

    for book in library.get_indexes_in_category('Torah'):
        book_element = root.find(book)
        for comment in util.traverse_ja(parsed_data[book], bottom=basestring):

            good_verse = True
            chapter, verse = comment['indices'][0], comment['indices'][1]

            # get the verse from the xml
            verse_element = book_element.find("./chapter[@chap_index='{}']/verse[@verse_index='{}']"
                                              .format(chapter+1, verse+1))
            rashis = Ref('Rashi on {}.{}.{}'.format(book, chapter+1, verse+1))
            total_rashis = len(rashis.all_subrefs())

            if verse_element is None:
                good_verse = False

            # compare number of Rashis on daat and sefaria. If only one Rashi link can be made
            elif total_rashis != int(verse_element.find('total_rashis').text) and total_rashis != 1:
                good_verse = False

            # compare number of siftei chakhmim on daat and Torat Emet
            elif len(parsed_data[book][chapter][verse]) != len(verse_element.findall('comment')):
                good_verse = False

            if good_verse:

                # grab the exact Rashi comment number to link to
                comment_number = comment['indices'][2]
                comment_element = verse_element.findall('comment')[comment_number]
                if total_rashis == 1:
                    rashi_value = 1
                else:
                    rashi_value = int(comment_element.attrib['rashi_comment'])

                refs = [u'Siftei Hakhamim, {}.{}.{}.{}'.format(book, *[x+1 for x in comment['indices']]),
                        u'Rashi on {}.{}.{}.{}'.format(book, chapter+1, verse+1, rashi_value)]

                # build the link object
                links.append({
                    'refs': refs,
                    'type': 'commentary',
                    'auto': False,
                    'generated_by': 'Siftei Hakhamim parse script'
                })

            else:
                bad_link = [book]
                bad_link.extend([x+1 for x in comment['indices']])
                url = 'draft.sefaria.org/Siftei_Hakhamim,_{}.{}.{}.{}'\
                    .format(book, *[x+1 for x in comment['indices']])
                bad_link.append(url)
                errors.append(bad_link)

    # write errors to csv file
    with open(error_file, 'w') as outfile:
        writer = csv.writer(outfile, delimiter=';')
        writer.writerow(['Book', 'Chapter', 'Verse', 'Comment', 'url'])
        writer.writerows(errors)

    return links


def rebuild_daat_file():
    xml = ET.ElementTree(ET.Element('root'))
    for book in library.get_indexes_in_category('Torah'):
        for ref in Ref(book).all_subrefs():
            parser = DaatRashiGrabber(ref)
            parser.add_to_xml(xml)

    xml.write('link_data2.xml')
    root = xml.getroot()
    for book in library.get_indexes_in_category('Torah'):
        for chapter in list(root.find(book)):
            recover_data(chapter)

    xml.write('fixed_links2.xml')


def build_index():

    books = library.get_indexes_in_category('Torah')

    # create index record
    record = SchemaNode()
    record.add_title('Siftei Hakhamim', 'en', primary=True, )
    record.add_title(u'שפתי חכמים', 'he', primary=True, )
    record.key = 'Siftei Hakhamim'

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
        "title": "Siftei Hakhamim",
        "categories": ["Commentary2", "Torah", "Rashi"],
        "schema": record.serialize()
    }
    return index


def post_text(parsed_data):

    for book in library.get_indexes_in_category('Torah'):
        version = {
            'versionTitle': 'Siftei Hakhamim',
            'versionSource': 'http://www.toratemetfreeware.com/',
            'language': 'he',
            'text': parsed_data[book]
        }
        functions.post_text('Siftei Hakhamim, {}'.format(book), version)


def manual_links():
    """
    Some links had to be created manually by the content team. The refs to link were saved in a
    csv
    :return: Json object of links parsed from the aforementioned csv.
    """

    with open('siftei hakhamim manual links.csv') as infile:
        csv_reader = ucsv.reader(infile, delimiter=';')
        links = [{'refs': [ref[0], ref[1]],
                  'type': 'commentary',
                  'auto': False,
                  'generated_by': 'Sefaria Content Team'}
                 for ref in csv_reader]
    return links


parsed = parse_multiple()
slinks = generate_links(parsed)
functions.post_index(build_index())
post_text(parsed)
functions.post_link(slinks)
functions.post_link(manual_links())
