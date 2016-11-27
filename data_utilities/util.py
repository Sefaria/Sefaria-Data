# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import os
import sys
import re
import codecs
from xml.etree import ElementTree as ET
p = os.path.dirname(os.path.abspath(__file__))+"/sources"
from sources.local_settings import *
sys.path.insert(0, p)
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.datatype import jagged_array
from urllib2 import HTTPError, URLError
import json
import urllib2
from sefaria.model import *

gematria = {}
gematria[u'א'] = 1
gematria[u'ב'] = 2
gematria[u'ג'] = 3
gematria[u'ד'] = 4
gematria[u'ה'] = 5
gematria[u'ו'] = 6
gematria[u'ז'] = 7
gematria[u'ח'] = 8
gematria[u'ט'] = 9
gematria[u'י'] = 10
gematria[u'כ'] = 20
gematria[u'ל'] = 30
gematria[u'מ'] = 40
gematria[u'נ'] = 50
gematria[u'ס'] = 60
gematria[u'ע'] = 70
gematria[u'פ'] = 80
gematria[u'צ'] = 90
gematria[u'ק'] = 100
gematria[u'ר'] = 200
gematria[u'ש'] = 300
gematria[u'ת'] = 400

wordToNumber = {}
wordToNumber[u'ראשון'] = 1
wordToNumber[u'שני'] = 2
wordToNumber[u'שלישי'] = 3
wordToNumber[u'רביעי'] = 4
wordToNumber[u'חמישי'] = 5
wordToNumber[u'ששי'] = 6
wordToNumber[u'שביעי'] = 7
wordToNumber[u'שמיני'] = 8
wordToNumber[u'תשיעי'] = 9
wordToNumber[u'עשירי'] = 10

class Util:
    def __init__(self, output_file, fail):
        self.output_file = output_file
        self.fail = fail

    def in_order_multiple_segments(self, line, curr_num, increment_by):
         if len(line) > 0 and line[0] == ' ':
             line = line[1:]
         if len(line) > 0 and line[len(line)-1] == ' ':
             line = line[:-1]
         if len(line.split(" "))>1:
             all = line.split(" ")
             num_list = []
             for i in range(len(all)):
                 num_list.append(getGematria(all[i]))
             num_list = sorted(num_list)
             for poss_num in num_list:
                 poss_num = fixChetHay(poss_num, curr_num)
                 if poss_num < curr_num:
                     return -1
                 else:
                     curr_num = poss_num
         return curr_num

    def fixChetHay(self, poss_num, curr_num):
        if poss_num == 8 and curr_num == 4:
            return 5
        elif poss_num == 5 and curr_num == 7:
            return 8
        else:
            return poss_num

    def in_order_caller(self, reg_exp_tag, file, reg_exp_reset):
        ##open file, create an array based on reg_exp,
        ##when hit reset_tag, call in_order
        in_order_array = []
        for line in open(file):
            reset = re.findall(reg_exp_reset, line)
            if len(reset) > 0:
                in_order(in_order_array, reg_exp_tag)
                in_order_array = []
            find_all = re.findall(reg_exp_tag, line)
            for each_one in find_all:
                in_order_array.append(each_one)
        in_order(in_order_array)




    def in_order(list, multiple_segments=False, dont_count=[], increment_by=1):
         poss_num = 0
         curr_num = 0
         perfect = True
         for line in list:
             for word in dont_count:
                line = line.replace(word, "")
             if multiple_segments == True:
                 curr_num = in_order_multiple_segments(line, curr_num, increment_by)
             else:
                 poss_num = getGematria(line)
                 poss_num = fixChetHay(poss_num, curr_num)
                 if increment_by > 0:
                     if poss_num - curr_num != increment_by:
                         perfect = False
                 if poss_num < curr_num:
                     perfect = False
                 curr_num = poss_num
                 if perfect == False:
                     self.fail()
                 prev_line = line

    def getHebrewTitle(sefer):
        sefer_url = SEFARIA_SERVER+'api/index/'+sefer.replace(" ","_")
        req = urllib2.Request(sefer_url)
        res = urllib2.urlopen(req)
        data = json.load(res)
        return data['heTitle']

    def convertDictToArray(dict, empty=[]):
        array = []
        count = 1
        text_array = []
        sorted_keys = sorted(dict.keys())
        for key in sorted_keys:
            if count == key:
                array.append(dict[key])
                count+=1
            else:
                diff = key - count
                while(diff>0):
                    array.append(empty)
                    diff-=1
                array.append(dict[key])
                count = key+1
        return array




    def wordHasNekudot(word):
        data = word.decode('utf-8')
        data = data.replace(u"\u05B0", "")
        data = data.replace(u"\u05B1", "")
        data = data.replace(u"\u05B2", "")
        data = data.replace(u"\u05B3", "")
        data = data.replace(u"\u05B4", "")
        data = data.replace(u"\u05B5", "")
        data = data.replace(u"\u05B6", "")
        data = data.replace(u"\u05B7", "")
        data = data.replace(u"\u05B8", "")
        data = data.replace(u"\u05B9", "")
        data = data.replace(u"\u05BB", "")
        data = data.replace(u"\u05BC", "")
        data = data.replace(u"\u05BD", "")
        data = data.replace(u"\u05BF", "")
        data = data.replace(u"\u05C1", "")
        data = data.replace(u"\u05C2", "")
        data = data.replace(u"\u05C3", "")
        data = data.replace(u"\u05C4", "")
        return data != word.decode('utf-8')


def isGematria(txt):
        txt = txt.replace('.','')
        if txt.find("ך")>=0:
            txt = txt.replace("ך", "כ")
        if txt.find("ם")>=0:
            txt = txt.replace("ם", "מ")
        if txt.find("ף")>=0:
            txt = txt.replace("ף", "פ")
        if txt.find("ץ")>=0:
            txt = txt.replace("ץ", "צ")
        if txt.find("טו")>=0:
            txt = txt.replace("טו", "יה")
        if txt.find("טז")>=0:
            txt = txt.replace("טז", "יו")
        if len(txt) == 2:
            letter_count = 0
            for i in range(9):
                if inv_gematria[i+1]==txt[letter_count:2+letter_count]:
                    return True
                if inv_gematria[(i+1)*10]==txt[letter_count:2+letter_count]:
                    return True
            for i in range(4):
                if inv_gematria[(i+1)*100]==txt[letter_count:2+letter_count]:
                    return True
        elif len(txt) == 4:
          first_letter_is = ""
          for letter_count in range(2):
            letter_count *= 2
            for i in range(9):
                if inv_gematria[i+1]==txt[letter_count:2+letter_count]:
                    if letter_count == 0:
                        #print "single false"
                        return False
                    else:
                        first_letter_is = "singles"
                if inv_gematria[(i+1)*10]==txt[letter_count:2+letter_count]:
                    if letter_count == 0:
                        first_letter_is = "tens"
                    elif letter_count == 2:
                        if first_letter_is != "hundred":
                            #print "tens false"
                            return False
            for i in range(4):
                if inv_gematria[(i+1)*100]==txt[letter_count:2+letter_count]:
                    if letter_count == 0:
                        first_letter_is = "hundred"
                    elif letter_count == 2:
                        if txt[0:2] != 'ת':
                            #print "hundreds false, no taf"
                            return False
        elif len(txt) == 6:
            #rules: first and second letter can't be singles
            #first letter must be hundreds
            #second letter can be hundreds or tens
            #third letter must be singles
            for letter_count in range(3):
                letter_count *= 2
                for i in range(9):
                    if inv_gematria[i+1]==txt[letter_count:2+letter_count]:
                        if letter_count != 4:
                        #	print "3 length singles false"
                            return False
                        if letter_count == 0:
                            first_letter_is = "singles"
                    if inv_gematria[(i+1)*10]==txt[letter_count:2+letter_count]:
                        if letter_count == 0:
                            #print "3 length tens false, can't be first"
                            return False
                        elif letter_count == 2:
                            if first_letter_is != "hundred":
                            #	print "3 length tens false because first letter not 100s"
                                return False
                        elif letter_count == 4:
                            #print "3 length tens false, can't be last"
                            return False
                for i in range(4):
                    if inv_gematria[(i+1)*100]==txt[letter_count:2+letter_count]:
                        if letter_count == 0:
                            first_letter_is = "hundred"
                        elif letter_count == 2:
                            if txt[0:2] != 'ת':
                                #print "3 length hundreds false, no taf"
                                return False
        else:
            print "length of gematria is off"
            print txt
            return False
        return True


def getGematria(txt):
        if not isinstance(txt, unicode):
            txt = txt.decode('utf-8')
        index=0
        sum=0
        while index <= len(txt)-1:
            if txt[index:index+1] in gematria:
                sum += gematria[txt[index:index+1]]

            index+=1
        return sum



def numToHeb(engnum=""):
        engnum = str(engnum)
        numdig = len(engnum)
        hebnum = ""
        letters = [["" for i in range(3)] for j in range(10)]
        letters[0]=["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
        letters[1]=["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
        letters[2]=["", "ק", "ר", "ש", "ת", "תק", "תר", "תש", "תת", "תתק"]
        if (numdig > 3):
            print "We currently can't handle numbers larger than 999"
            exit()
        for count in range(numdig):
            hebnum += letters[numdig-count-1][int(engnum[count])]
        hebnum = re.sub('יה', 'טו', hebnum)
        hebnum = re.sub('יו', 'טז', hebnum)
        hebnum = hebnum.decode('utf-8')
        return hebnum


def multiple_replace(old_string, replacement_dictionary):
        """
        Use a dictionary to make multiple replacements to a single string

        :param old_string: String to which replacements will be made
        :param replacement_dictionary: a dictionary with keys being the substrings
        to be replaced, values what they should be replaced with.
        :return: String with replacements made.
        """

        for keys, value in replacement_dictionary.iteritems():
            old_string = old_string.replace(keys, value)

        return old_string


def find_discrepancies(book_list, version_title, file_buffer, language, middle=False):
        """
        Prints all cases in which the number of verses in a text version doesn't match the
        number in the canonical version.

        *** Only works for Tanach, can be modified to work for any level 2 text***

        :param book_list: list of books
        :param version_title: Version title to be examined
        :param file_buffer: Buffer for file to print results
        :param language: 'en' or 'he' accordingly
        :param middle: set to True to manually start scanning a book from the middle.
        If middle is set to True, user will be prompted for the beginning chapter.
        """

        # loop through each book
        for book in book_list:

            # print book to give user update on progress
            print book
            book = book.replace(' ', '_')
            book = book.replace('\n', '')

            if middle:

                print "Start {0} at chapter: ".format(book)
                start_chapter = input()
                url = SEFARIA_SERVER + '/api/texts/' + book + '.' + \
                    str(start_chapter) + '/' + language + '/' + version_title

            else:
                url = SEFARIA_SERVER + '/api/texts/' + book + '.1/' + language + '/' + version_title


            try:
                # get first chapter in book
                response = urllib2.urlopen(url)
                version_text = json.load(response)

                # loop through chapters
                chapters = Ref(book).all_subrefs()

                # check for correct number of chapters
                if len(chapters) != version_text['lengths'][0]:
                    file_buffer.write('Chapter Problem in'+book+'\n')

                for index, chapter in enumerate(chapters):

                    # if starting in the middle skip to appropriate chapter
                    if middle:
                        if index+1 != start_chapter:
                            continue

                        else:
                            # set middle back to false
                            middle = False

                    print index+1,

                    # get canonical number of verses
                    canon = len(TextChunk(chapter, vtitle=u'Tanach with Text Only', lang='he').text)

                    # get number of verses in version
                    verses = len(version_text['text'])
                    if verses != canon:
                        file_buffer.write(chapter.normal() + '\n')

                    # get next chapter
                    next_chapter = replace_using_regex(' \d', version_text['next'], ' ', '.')
                    next_chapter = next_chapter.replace(' ', '_')
                    url = SEFARIA_SERVER+'/api/texts/'+next_chapter+'/'+language+'/'+version_title

                    response = urllib2.urlopen(url)
                    version_text = json.load(response)

            except (URLError, HTTPError, KeyboardInterrupt, KeyError, ValueError) as e:
                print e
                print url
                file_buffer.close()
                sys.exit(1)


def jagged_array_to_file(output_file, jagged_array, section_names):
    """
    Prints contents of a jagged array to a file. Recursive.
    :param output_file: File to write data.
    :param jagged_array: Multi dimensional array. Lowest level array should be strings.
    :param section_names: Names of segments to be printed in files (chapters, verse, siman, mishna etc.)
    Length must equal dimensions of jagged array.
    """

    for index, item in enumerate(jagged_array):
        output_file.write(u'{} {}:\n'.format(section_names[0], index+1))

        if type(item) is str or type(item) is unicode:
            output_file.write(u'{}\n'.format(item))

        elif type(item) is list:
            jagged_array_to_file(output_file, item, section_names[1:])

        else:
            print 'jagged array contains unknown type'
            output_file.close()
            raise TypeError


def ja_to_xml(ja, section_names, filename='output.xml'):
    """
    Takes a jagged array and prints an xml file
    :param ja: list or nested list, bottom must be string or unicode
    :param section_names: list of names with which to identify sections (E.g. ['Chapter', 'Verse'])
    Length must match depth of of jagged_array
    :param filename: Name of file to output result.
    """
    def build_xml(data, sections, parent):

        for index, item in enumerate(data):
            child = ET.SubElement(parent, sections[0], attrib={'index': str(index+1)})

            if isinstance(item, basestring):
                child.text = item

            elif isinstance(item, list):
                build_xml(item, sections[1:], parent=child)

            else:
                raise TypeError('Jagged Array contains unknown type')

    root = ET.Element('root')
    build_xml(ja, section_names, root)
    tree = ET.ElementTree(root)
    tree.write(filename, 'utf-8')


def file_to_ja(depth, infile, expressions, cleaner, grab_all=False):
    """
    Designed to be the first stage of a reusable parsing tool. Adds lines of text to the Jagged
    Array in the desired structure (Chapter, verse, etc.)
    :param depth: depth of the JaggedArray.
    :param infile: Text file to read from
    :param expressions: A list of regular expressions with which to identify section (chapter) level. Do
    not include an expression with which to break up the segment levels.
    :param cleaner: A function that takes a list of strings and returns an array with the text parsed
    correctly. Should also break up and remove unnecessary tagging data.
    :param grab_all: If set to true, will grab the lines indicating new sections.
    :return: A jagged_array with the text properly structured.
    """

    # instantiate ja
    structure = reduce(lambda x, y: [x], range(depth-1), [])
    ja = jagged_array.JaggedArray(structure)

    # ensure there is a regex for every level except the lowest
    if depth - len(expressions) != 1:
        raise AttributeError('Not enough data to parse. Need {} expressions, '
                             'received {}'.format(depth-1, len(expressions)))

    # compile regexes, instantiate index list
    regexes, indices = [re.compile(ex) for ex in expressions], [-1]*len(expressions)
    temp = []

    # loop through file
    for line in infile:

        # check for matches to the regexes
        for i, reg in enumerate(regexes):

            if reg.search(line):
                # check that we've hit the first chapter and verse
                if indices.count(-1) == 0:
                    ja.set_element(indices, cleaner(temp))
                    temp = []

                    if grab_all:
                        temp.append(line)

                # increment index that's been hit, reset all subsequent indices
                indices[i] += 1
                indices[i+1:] = [-1 if x >= 0 else x for x in indices[i+1:]]
                break

        else:
            if indices.count(-1) == 0:
                temp.append(line)
    else:
        ja.set_element(indices, cleaner(temp))

    return ja


def he_array_to_int(he_array):
    """
    Takes an array of hebrew numbers (א,ב, י"א...) and returns array of integers.
    :param he_array: Array of hebrew letters which represents numbers
    :return: Array of numbers
    """

    numbers = []
    for he in he_array:
        numbers.append(getGematria(he.replace(u'"', u'')))
    return numbers


def replace_using_regex(regex, query, new):
    """
    This is an enhancement of str.replace(). It will only call str.replace if the regex has
    been found, thus allowing replacement of tags that may serve multiple or ambiguous functions.
    Should there be a need, an endline parameter can be added which will be appended to the end of
    the string
    :param regex: A regular expression. Will be compiled locally.
    :param query: The input string to be examined.
    :param new: The text that will be inserted instead of 'old'.
    :return: A new string with 'old' replaced by 'new'.
    """

    # compile regex and search
    reg = re.compile(regex)
    result = re.search(reg, query)
    if result:

        # get all instances of match
        matches = re.finditer(reg, query)
        for match in matches:
            temp = match.group()
            query = query.replace(temp, new)
    return query


def clean_jagged_array(messy_array, strip_list):
    """
    Given a jagged array and a list of regexes, return a new jagged array with all cases in regex list
    striped out.
    :param messy_array: Jagged array to be cleaned
    :param strip_list: list of strings or regular expressions to be stripped from jagged array
    :return: New jagged array with all cases in strip_list removed.
    """

    clean_array = []

    for item in messy_array:

        if type(item) is list:
            clean_array.append(clean_jagged_array(item, strip_list))

        elif type(item) is str or type(item) is unicode:

            for case in strip_list:
                item = re.sub(case, u'', item)
            item = re.sub(u' +', u' ', item)
            clean_array.append(item.lstrip(u' '))

        else:
            print 'Jagged array contains unknown type'
            raise TypeError

    return clean_array


def traverse_ja(ja, indices=None, bottom=unicode):
    """
    A generator to move through a JaggedArray like structure, retrieving the indices  of each element of
    the JA as you go.
    :param ja: JaggedArray like object to traverse
    :param indices: List of indices needed to locate the first element of the array. Leave empty if
    starting from the root.
    :param bottom: Data type at the bottom of the array. Used as a terminating condition.
    :yield: Dictionary with the keys indices and data, corresponding to the retrieved data and its
    corresponding address.
    """
    if indices is None:
        indices = []

    if isinstance(ja, bottom):
        yield {'data': ja, 'indices': indices}

    else:
        for index, data in enumerate(ja):
            if index == 0:
                indices.append(index)
            else:
                indices[-1] = index
            if data:
                for thing in traverse_ja(data, indices, bottom):
                    yield thing
        indices.pop()


def grab_section_names(section_expression, input_file, group_number=0):
    """
    Grab the names of the sections that need to be converted into a complex text
    :param section_expression: An expression that can be compiled into a regex that will find
     the corresponding sections
    :param input_file: File from which to grab the results
    :param group_number: If needed, supply the capture group that will return the correct name.
    :return: List of strings.
    """

    section_reg = re.compile(section_expression)
    names = []

    for line in input_file:

        found_match = section_reg.search(line)
        if found_match:
            names.append(found_match.group(group_number))

    return names


def simple_to_complex(segment_names, jagged_text_array):
    """
    Given a simple text and the names of each section, convert a simple text into a complex one.
    :param segment_names: A list of names for each section
    :param jagged_text_array: A parsed jagged array to be converted from a simple to a complex text
    :return: Dictionary representing the complex text structure
    """

    # Ensure there are the correct number of segment names
    if len(segment_names) != len(jagged_text_array):
        raise IndexError('Length of segment_names does not match length of jaggedArray')

    complex_text = {}

    for index, name in enumerate(segment_names):
        complex_text[name] = jagged_text_array[index]

    return complex_text


def convert_dict_to_array(dictionary):

    array = []
    count = 1
    sorted_keys = sorted(dictionary.keys())

    for key in sorted_keys:

        if count == key:

            array.append(dictionary[key])
            count += 1

        else:
            diff = key - count

            while diff > 0:
                array.append([])
                diff -= 1

            array.append(dictionary[key])
            count = key+1

    return array


def restructure_file(filename, function, *args):
    """
    Restructures a file according to function
    :param filename:
    :param function:
    :param args:
    """
    original = codecs.open(filename, 'r', 'utf-8')
    updated = codecs.open(u'{}.tmp'.format(filename), 'w', 'utf-8')

    for line in original:
        new_line = function(line, *args)
        updated.write(new_line)

    original.close()
    updated.close()

    os.remove(filename)
    os.rename(u'{}.tmp'.format(filename), filename)


class ToratEmetData:
    """
    Base class for parsing HTML downloaded from Torat Emet. Strategy is to iterate through the data line
    by line, identifying lines that contain important data. These lines can then be fed through an html
    parser (such as Beautiful soup) for cleanup and identification, and then ultimately structured into
    a proper jagged array or dictionary of jagged arrays.
    """

    def __init__(self, path, from_url=False, codec='cp1255'):
        """

        :param path: Path to file or url
        :param from_url: Set to True if data must be downloaded from url
        :param codec:
        """
        self._path = path
        self._from_url = from_url
        self._codec = codec
        self.lines = self._get_lines()
        self._important_lines = self._extract_important_data()
        self.parsed_text = self._parse()

    def _get_lines(self):

        if self._from_url:
            lines = []
            for line in urllib2.urlopen(self._path).readlines():
                lines.append(line.decode(self._codec))
            return lines

        else:
            with codecs.open(self._path, 'r', self._codec) as infile:
                return infile.readlines()

    def _extract_important_data(self):
        raise NotImplementedError

    @staticmethod
    def build_segments(section):

        comments = []

        bold = re.compile(u'<b>')
        if not bold.search(section):
            return [section]
        matches = bold.finditer(section)
        start = next(matches)

        for next_match in matches:
            comments.append(section[start.start(): next_match.start()])
            start = next_match
        else:
            comments.append(section[start.start():])
        return comments

    def _parse(self):

        book = {}
        for line in self._important_lines:
            chapter, verse = line['chapter'], line['verse']

            if chapter not in book.keys():
                book[chapter] = {}

            book[chapter][verse] = self.build_segments(line['text'])

        for key in book.keys():
            book[key] = convert_dict_to_array(book[key])

        book = convert_dict_to_array(book)
        return book


def get_cards_from_trello(list_name, board_json):
    """
    Trello can export a board as a JSON object. Use this function to grab the names of all the cards that
    belong to a certain list on the board.
    :param list_name: Name of the list that holds the cards of interest
    :param board_json: The exported JSON file from trello that relates to the board of interest
    :return: A list of all the cards on the specified Trello list.
    """

    board = json.loads(board_json.read())

    list_id = u''
    for column in board['lists']:
        if column['name'] == list_name:
            list_id = column['id']

    cards = []
    for card in board['cards']:
        if card['idList'] == list_id:
            cards.append(card['name'])

    return cards


class WeightedLevenshtein:
    """
    Use this class to calculate the Weighted Levenshtein between strings. The default letter frequencies defined here
    are based off of the Talmud. The default min_cost value is recommended, and should only be changed by engineers with
    a proficient understanding of the weighted Levenshtein algorithm.
    """

    def __init__(self, letter_freqs=None, min_cost=None):

        if letter_freqs is None:
            self.letter_freqs = {
                u'י': 0.0,
                u'ו': 0.2145,
                u'א': 0.2176,
                u'מ': 0.3555,
                u'ה': 0.4586,
                u'ל': 0.4704,
                u'ר': 0.4930,
                u'נ': 0.5592,
                u'ב': 0.5678,
                u'ש': 0.7007,
                u'ת': 0.7013,
                u'ד': 0.7690,
                u'כ': 0.8038,
                u'ע': 0.8362,
                u'ח': 0.8779,
                u'ק': 0.9124,
                u'פ': 0.9322,
                u'ס': 0.9805,
                u'ט': 0.9924,
                u'ז': 0.9948,
                u'ג': 0.9988,
                u'צ': 1.0
            }
        else:
            self.letter_freqs = letter_freqs

        self.sofit_map = {
            u'ך': u'כ',
            u'ם': u'מ',
            u'ן': u'נ',
            u'ף': u'פ',
            u'ץ': u'צ',
        }

        if min_cost is None:
            self.min_cost = 1.0
        else:
            self.min_cost = min_cost

    def sofit_swap(self, c):
        return self.sofit_map.get(c, c)

    def cost(self, c1, c2=None):
        c1 = self.sofit_swap(c1)
        c2 = self.sofit_swap(c2)
        w1 = self.letter_freqs[c1] if c1 in self.letter_freqs else 0.0
        if c2:
            w2 = self.letter_freqs[c2] if c2 in self.letter_freqs else 0.0
            return w1 + self.min_cost if w1 > w2 else w2 + self.min_cost
        else:
            return w1 + self.min_cost

    def calculate(self, s1, s2, normalize=True):
        """
        This method calculates the Weighted Levenshtein between two strings. It should be noted however that the
        Levenshtein score between two strings is dependant on the lengths of the two strings. Therefore, it is possible
        that two short strings with a low Levenshtein score may score more poorly than two long strings with a higher
        Levenshtien score.

        The code for this method is redacted from https://en.wikipedia.org/wiki/Levenshtein_distance. As we are only
        calculating the distance, without building an alignment, we only save two rows of the Levenshtein matrix at
        any given time.
        :param s1: First string. Determines the number of rows in the Levenshtein matrix.
        :param s2: Second string. Determines the number of columns in the Levenshtein matrix.
        :param normalize: True to get a score between 0-100, False to get the weighted Levenshtein score.
        :return: If normalize is True, will return an integer between 0-100, with 100 being a perfect match and 0 being
        two ompletely different strings with the most expensive swap at every location. Otherwise, the exact weighted
        Levenshtein score will be returned.
        """
        if s1 == s2:
            score = 0

        else:
            """
            v0 corresponds to row i-1 in the Levenshtein matrix, where i is the index of the current letter in s1.
            It is initialized to the cost of deleting every letter in s2 up to letter j for each letter j in s2
            v1 corresponds to row i of the Levenshtein matrix.
            """
            v0 = []
            for j in xrange(len(s2) + 1):
                if j == 0:
                    v0.append(0)
                else:
                    v0.append(self.cost(s2[j-1]) + v0[j-1])
            v1 = [0] * (len(s2) + 1)

            for i in xrange(len(s1)):
                v1[0] = self.cost(s1[i])  # Set to the cost of inserting the first char of s1 into s2
                for j in xrange(len(s2)):
                    cost_sub = 0.0 if (self.sofit_swap(s1[i]) == self.sofit_swap(s2[j])) else self.cost(s1[i], s2[j])
                    cost_ins = self.cost(s2[j])
                    cost_del = self.cost(s1[i])
                    v1[j+1] = min(v1[j]+cost_ins, min(v0[j+1]+cost_del, v0[j]+cost_sub))

                vtemp = v0
                v0 = v1
                v1 = vtemp
            score = v0[-1]

        if normalize:
            expensive = max(self.letter_freqs.values())
            length = max(len(s1), len(s2))
            max_score = length * (expensive + self.min_cost)
            return int(100.0*(1 - (score / max_score)))

        else:
            return score

