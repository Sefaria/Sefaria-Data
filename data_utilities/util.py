# -*- coding: utf-8 -*-
import os
import sys
import re
import math
import codecs
from bisect import bisect_right
from typing import Callable
from collections import defaultdict
from xml.etree import ElementTree as ET
from urllib.error import HTTPError, URLError
import json
import urllib.request, urllib.error, urllib.parse
from functools import reduce, lru_cache
import itertools
from typing import List

try:
    p = os.path.dirname(os.path.abspath(__file__))+"/sources"
    from sources.local_settings import *
    sys.path.insert(0, p)
    sys.path.insert(0, SEFARIA_PROJECT_PATH)
except ImportError:
    pass
from sefaria.datatype import jagged_array
from sefaria.model import *
from sefaria.model.schema import TitleGroup


gematria = {}
gematria['א'] = 1
gematria['ב'] = 2
gematria['ג'] = 3
gematria['ד'] = 4
gematria['ה'] = 5
gematria['ו'] = 6
gematria['ז'] = 7
gematria['ח'] = 8
gematria['ט'] = 9
gematria['י'] = 10
gematria['כ'] = 20
gematria['ך'] = 20
gematria['ל'] = 30
gematria['מ'] = 40
gematria['ם'] = 40
gematria['נ'] = 50
gematria['ן'] = 50
gematria['ס'] = 60
gematria['ע'] = 70
gematria['פ'] = 80
gematria['ף'] = 80
gematria['צ'] = 90
gematria['ץ'] = 90
gematria['ק'] = 100
gematria['ר'] = 200
gematria['ש'] = 300
gematria['ת'] = 400

inv_gematria = {value: key for key, value in gematria.items()}

wordToNumber = {}
wordToNumber['ראשון'] = 1
wordToNumber['שני'] = 2
wordToNumber['שלישי'] = 3
wordToNumber['רביעי'] = 4
wordToNumber['חמישי'] = 5
wordToNumber['ששי'] = 6
wordToNumber['שביעי'] = 7
wordToNumber['שמיני'] = 8
wordToNumber['תשיעי'] = 9
wordToNumber['עשירי'] = 10

he_char_ord = {
    'א': 1,
    'ב': 2,
    'ג': 3,
    'ד': 4,
    'ה': 5,
    'ו': 6,
    'ז': 7,
    'ח': 8,
    'ט': 9,
    'י': 10,
    'כ': 11,
    'ך': 11,
    'ל': 12,
    'מ': 13,
    'ם': 13,
    'נ': 14,
    'ן': 14,
    'ס': 15,
    'ע': 16,
    'פ': 17,
    'ף': 17,
    'צ': 18,
    'ץ': 18,
    'ק': 19,
    'ר': 20,
    'ש': 21,
    'ת': 22
}

num_to_char_dict = {1: "א",
2: "ב",
3: "ג",
4: "ד",
5: "ה",
6: "ו",
7: "ז",
8: "ח",
9: "ט",
10: "י",
11: "כ",
12: "ל",
13: "מ",
14: "נ",
15: "ס",
16: "ע",
17: "פ",
18: "צ",
19: "ק",
20: "ר",
21: "ש",
22: "ת",
}


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
            print("length of gematria is off")
            print(txt)
            return False
        return True


class StructuredDocument:
    """
    class for extracting specific parts (i.e. chapters) of a text file. Pieces that exist outside the structure (an intro
    for example) will be included, but they will not be as easily accessible as the chapters.
    """

    def __init__(self, filepath, regex):
        with codecs.open(filepath, 'r', 'utf-8') as infile:
            lines = infile.readlines()

        sections, section_mapping = [], {}
        current_section, section_num, section_index = [], None, 0

        for line in lines:
            match = re.search(regex, line)
            if match:
                if len(current_section) > 0:
                    sections.append(''.join(current_section))
                    if section_num:
                        section_mapping[section_num] = section_index
                    section_index += 1
                    current_section = []
                section_num = getGematria(match.group(1))

            current_section.append(line)
        else:
            sections.append(''.join(current_section))
            section_mapping[section_num] = section_index

        self._sections = sections
        self._section_mapping = section_mapping

    def get_section(self, section_number):
        section_index = self._section_mapping[section_number]
        return self._sections[section_index]

    def _set_section(self, section_number, new_section):
        section_index = self._section_mapping[section_number]
        self._sections[section_index] = new_section

    def edit_section(self, section_number, callback, *args, **kwargs):
        old_section = self.get_section(section_number)
        new_section = callback(old_section, *args, **kwargs)
        self._set_section(section_number, new_section)

    def get_whole_text(self):
        return ''.join(self._sections)

    def write_to_file(self, filename):
        with codecs.open(filename, 'w', 'utf-8') as outfile:
            outfile.write(self.get_whole_text())

    def get_chapter_values(self):
        return sorted(self._section_mapping.keys())


def getGematria(txt):
        if not isinstance(txt, str):
            txt = txt.decode('utf-8')
        index=0
        sum=0
        while index <= len(txt)-1:
            if txt[index:index+1] in gematria:
                sum += gematria[txt[index:index+1]]

            index+=1
        return sum


def he_ord(he_char):
    """
    Get the order number for a hebrew character (א becomes 1, ת becomes 22). Sofi letters (i.e ך), return the same value
    as their regular
    :param he_char:
    :return:
    """
    if len(he_char) != 1:
        raise AssertionError('Can only evaluate a single character')
    if re.search('[\u05d0-\u05ea]', he_char) is None:
        raise AssertionError('{} is not a Hebrew Character!'.format(he_char))
    return he_char_ord[he_char]


def he_num_to_char(num):
    assert 1 <= num <= 22
    return num_to_char_dict[num]



def numToHeb(engnum=""):
        engnum = str(engnum)
        numdig = len(engnum)
        hebnum = ""
        letters = [["" for i in range(3)] for j in range(10)]
        letters[0]=["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
        letters[1]=["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
        letters[2]=["", "ק", "ר", "ש", "ת", "תק", "תר", "תש", "תת", "תתק"]
        if (numdig > 3):
            sub_engnum = int(engnum)-800
            if sub_engnum>400:
                raise KeyError
            return "תת{}".format(numToHeb(sub_engnum))
        for count in range(numdig):
            hebnum += letters[numdig-count-1][int(engnum[count])]
        hebnum = re.sub('יה', 'טו', hebnum)
        hebnum = re.sub('יו', 'טז', hebnum)
        # hebnum = hebnum.decode('utf-8')
        return hebnum


def multiple_replace(old_string, replacement_dictionary, using_regex = False):
        """
        Use a dictionary to make multiple replacements to a single string

        :param old_string: String to which replacements will be made
        :param replacement_dictionary: a dictionary with keys being the substrings
        to be replaced, values what they should be replaced with.
        :param 'regex = True' uses re.sub rather then str.replace
        :return: String with replacements made.
        """
        if using_regex:
            for keys, value in replacement_dictionary.items():
                old_string = re.sub(keys,value,old_string)
        else:
            for keys, value in replacement_dictionary.items():
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
            print(book)
            book = book.replace(' ', '_')
            book = book.replace('\n', '')

            if middle:

                print("Start {0} at chapter: ".format(book))
                start_chapter = eval(input())
                url = SEFARIA_SERVER + '/api/texts/' + book + '.' + \
                    str(start_chapter) + '/' + language + '/' + version_title

            else:
                url = SEFARIA_SERVER + '/api/texts/' + book + '.1/' + language + '/' + version_title


            try:
                # get first chapter in book
                response = urllib.request.urlopen(url)
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

                    print(index+1)

                    # get canonical number of verses
                    canon = len(TextChunk(chapter, vtitle='Tanach with Text Only', lang='he').text)

                    # get number of verses in version
                    verses = len(version_text['text'])
                    if verses != canon:
                        file_buffer.write(chapter.normal() + '\n')

                    # get next chapter
                    next_chapter = replace_using_regex(' \d', version_text['next'], ' ', '.')
                    next_chapter = next_chapter.replace(' ', '_')
                    url = SEFARIA_SERVER+'/api/texts/'+next_chapter+'/'+language+'/'+version_title

                    response = urllib.request.urlopen(url)
                    version_text = json.load(response)

            except (URLError, HTTPError, KeyboardInterrupt, KeyError, ValueError) as e:
                print(e)
                print(url)
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
        output_file.write('{} {}:\n'.format(section_names[0], index+1))

        if type(item) is str or type(item) is str:
            output_file.write('{}\n'.format(item))

        elif type(item) is list:
            jagged_array_to_file(output_file, item, section_names[1:])

        else:
            print('jagged array contains unknown type')
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

            if isinstance(item, str):
                child.text = item

            elif isinstance(item, list):
                build_xml(item, sections[1:], parent=child)

            else:
                raise TypeError('Jagged Array contains unknown type')

    root = ET.Element('root')
    build_xml(ja, section_names, root)
    tree = ET.ElementTree(root)
    tree.write(filename, encoding="unicode")


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
    structure = reduce(lambda x, y: [x], list(range(depth-1)), [])
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


def file_to_ja_g(depth, infile, expressions, cleaner, gimatria=False, group_name='gim', grab_all=None):
    """
    like file to ja but with changing the numbers to Gimatria
    Designed to be the first stage of a reusable parsing tool. Adds lines of text to the Jagged
    Array in the desired structure (Chapter, verse, etc.)
    :param depth: depth of the JaggedArray.
    :param infile: Text file to read from
    :param expressions: A list of regular expressions with which to identify section (chapter) level. Do
    not include an expression with which to break up the segment levels.
    :param cleaner: A function that takes a list of strings and returns an array with the text parsed
    correctly. Should also break up and remove unnecessary tagging data.
    :param grab_all: a boolean list according to the regexs, if True then grab all of that if False erase line
            the 5 is just above the 3 which is the deepest length we use for now.
    :param gimatria: if the text is presented with gimatria in it.
    :param group_name: a name given to the group of letters for the gimatria to actually use
    :return: A jagged_array with the text properly structured.
    """

    if grab_all is None:
        grab_all = [False] * len(expressions)

    # instantiate ja
    structure = reduce(lambda x, y: [x], list(range(depth - 1)), [])
    ja = jagged_array.JaggedArray(structure)

    # ensure there is a regex for every level except the lowest
    if depth - len(expressions) != 1:
        raise AttributeError('Not enough data to parse. Need {} expressions, '
                             'received {}'.format(depth - 1, len(expressions)))

    # compile regexes, instantiate index list
    regexes, indices = [re.compile(ex) for ex in expressions], [-1] * len(expressions)
    temp = []

    # loop through file
    for line in infile:

        # check for matches to the regexes
        for i, reg in enumerate(regexes):
            found = reg.search(line)
            if found:

                if indices.count(-1) == 0:
                    ja.set_element(indices, cleaner(temp), [])
                    temp = []
                if grab_all[i]:
                    temp.append(line)
                    # increment index that's been hit, reset all subsequent indices
                if gimatria:  # note: if you uncomment the top must make this elif
                    gimt = getGematria(found.group('{}'.format(group_name)))
                    if gimt != 0:  # increment index that's been hit, reset all subsequent indices
                        indices[i] = gimt - 1
                    else:
                        indices[i] += 1
                else:
                    indices[i] += 1
                indices[i + 1:] = [-1 if x >= 0 else x for x in indices[i + 1:]]
                break

        else:
            if indices.count(-1) == 0:
                temp.append(line)
    else:
        ja.set_element(indices, cleaner(temp), [])

    return ja

def he_array_to_int(he_array):
    """
    Takes an array of hebrew numbers (א,ב, י"א...) and returns array of integers.
    :param he_array: Array of hebrew letters which represents numbers
    :return: Array of numbers
    """

    numbers = []
    for he in he_array:
        numbers.append(getGematria(he.replace('"', '')))
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

        elif type(item) is str or type(item) is str:

            for case in strip_list:
                item = re.sub(case, '', item)
            item = re.sub(' +', ' ', item)
            clean_array.append(item.lstrip(' '))

        else:
            print('Jagged array contains unknown type')
            raise TypeError

    return clean_array


def traverse_ja(ja, indices=None, bottom=str):
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
                for thing in traverse_ja(data, indices[:], bottom):
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


def convert_dict_to_array(dictionary, default_value=list):
    assert all([isinstance(item, int) for item in list(dictionary.keys())])
    assert callable(default_value)

    output_list = list()
    dictionary = defaultdict(default_value, dictionary)
    for key in range(max(dictionary.keys()) + 1):
        output_list.append(dictionary[key])
    return output_list


def restructure_file(filename, function, *args):
    """
    Restructures a file according to function
    :param filename:
    :param function:
    :param args:
    """
    original = codecs.open(filename, 'r', 'utf-8')
    updated = codecs.open('{}.tmp'.format(filename), 'w', 'utf-8')

    for line in original:
        new_line = function(line, *args)
        updated.write(new_line)

    original.close()
    updated.close()

    os.remove(filename)
    os.rename('{}.tmp'.format(filename), filename)


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
            for line in urllib.request.urlopen(self._path).readlines():
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

        bold = re.compile('<b>')
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

            if chapter not in list(book.keys()):
                book[chapter] = {}

            book[chapter][verse] = self.build_segments(line['text'])

        for key in list(book.keys()):
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

    list_id = ''
    for column in board['lists']:
        if column['name'] == list_name:
            list_id = column['id']

    cards = []
    for card in board['cards']:
        if card['idList'] == list_id:
            cards.append(card['name'])

    return cards


class LevenshteinError(Exception):
    pass


class WeightedLevenshtein:
    """
    Use this class to calculate the Weighted Levenshtein between strings. The default letter frequencies defined here
    are based off of the Talmud. The default min_cost value is recommended, and should only be changed by engineers with
    a proficient understanding of the weighted Levenshtein algorithm.
    """

    def __init__(self, letter_freqs=None, min_cost=None, swap_costs=None):
        """
        :param swap_costs: dict of form `{(c1, c2): cost}` where `c1` and `c2` are two characters and `cost` is the cost for swapping them. overides costs listed in `letter_freqs`
        """
        if letter_freqs is None:
            self.letter_freqs = {
                'י': 0.0,
                'ו': 0.2145,
                'א': 0.2176,
                'מ': 0.3555,
                'ה': 0.4586,
                'ל': 0.4704,
                'ר': 0.4930,
                'נ': 0.5592,
                'ב': 0.5678,
                'ש': 0.7007,
                'ת': 0.7013,
                'ד': 0.7690,
                'כ': 0.8038,
                'ע': 0.8362,
                'ח': 0.8779,
                'ק': 0.9124,
                'פ': 0.9322,
                'ס': 0.9805,
                'ט': 0.9924,
                'ז': 0.9948,
                'ג': 0.9988,
                'צ': 1.0
            }
        else:
            self.letter_freqs = letter_freqs

        self.sofit_map = {
            'ך': 'כ',
            'ם': 'מ',
            'ן': 'נ',
            'ף': 'פ',
            'ץ': 'צ',
        }

        if min_cost is None:
            self.min_cost = 1.0
        else:
            self.min_cost = min_cost

        #self._cost is a dictionary with keys either single letters, or tuples of two letters.
        # note that for calculate, we remove the sofit letters.  We could probably remove them from here as well, save for cost_str().
        all_letters = list(self.letter_freqs.keys()) + list(self.sofit_map.keys())
        self._cost = defaultdict(lambda: self.min_cost)
        self._cost.update({c: self._build_cost(c) for c in all_letters})  # single letters
        self._cost.update({(c1, c2): self._build_cost(c1, c2) for c1 in all_letters for c2 in all_letters}) # tuples
        if swap_costs is not None:
            self._cost.update(swap_costs)

        self._most_expensive = max(self.letter_freqs.values())

        # dict((ord(char), sofit_map[char]) for char in self.sofit_map.keys())
        self._sofit_transx_table = {
            1498: '\u05db',
            1501: '\u05de',
            1503: '\u05e0',
            1507: '\u05e4',
            1509: '\u05e6'
        }
    #Cost of calling this isn't worth the syntax benefit
    """
    def sofit_swap(self, c):
        return self.sofit_map.get(c, c)
    """


    #This is a pure function with limited inputs.  Building as a lookup saves lots of time.
    def _build_cost(self, c1, c2=None):
        c1 = self.sofit_map.get(c1, c1)
        c2 = self.sofit_map.get(c2, c2)
        w1 = self.letter_freqs[c1] if c1 in self.letter_freqs else 0.0
        if c2:
            w2 = self.letter_freqs[c2] if c2 in self.letter_freqs else 0.0
            return w1 + self.min_cost if w1 > w2 else w2 + self.min_cost
        else:
            return w1 + self.min_cost

    # used?
    def cost_str(self, string):
        cost = 0
        for c in string:
            cost += self._cost[c]
        return cost

    _calculate_cache = {}
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
        original_s1, original_s2 = s1, s2
        if not self._calculate_cache.get((original_s1, original_s2, normalize), None):
            s1_len = len(s1)
            s2_len = len(s2)


            if s1_len == 0 and s2_len == 0 and normalize:
                raise LevenshteinError("both strings can't be empty with normalize=True. leads to divide by zero")

            if s1 == s2:
                score = 0

            else:
                """
                v0 corresponds to row i-1 in the Levenshtein matrix, where i is the index of the current letter in s1.
                It is initialized to the cost of deleting every letter in s2 up to letter j for each letter j in s2
                v1 corresponds to row i of the Levenshtein matrix.
                """
                s1 = s1.translate(self._sofit_transx_table)
                s2 = s2.translate(self._sofit_transx_table)
                s1_cost = [self._cost[c] for c in s1]
                s2_cost = [self._cost[c] for c in s2]
                total_delete_cost = 0
                v0 = [0]
                for j in range(s2_len):
                    v0 += [s2_cost[j] + v0[j]]
                v1 = [0] * (s2_len + 1)

                for i in range(s1_len):
                    cost_del = s1_cost[i]
                    v1[0] = total_delete_cost = cost_del + total_delete_cost  # Set to cost of deleting char from s1
                    for j in range(s2_len):
                        cost_ins = s2_cost[j]
                        cost_sub = 0.0 if s1[i] == s2[j] else self._cost.get(
                            (s1[i], s2[j]), cost_ins if cost_ins > cost_del else cost_del)
                        v1[j + 1] = min(v1[j] + cost_ins, v0[j + 1] + cost_del, v0[j] + cost_sub)

                    v0, v1 = v1, v0
                score = v0[-1]

            if normalize:
                length = max(s1_len, s2_len)
                max_score = length * (self._most_expensive + self.min_cost)
                self._calculate_cache[(original_s1, original_s2, normalize)] = int(100.0 * (1 - (score / max_score)))

            else:
                self._calculate_cache[(original_s1, original_s2, normalize)] = score

        return self._calculate_cache[(original_s1, original_s2, normalize)]

    def calculate_best(self, s, words, normalize=True):
        """
        :param s: str
        :param words: list of str
        :return: the lowest distance for s in words and return the index and distance
        """
        best_dist = 0 if normalize else 10000 # large number
        best_ind = -1
        for i, w in enumerate(words):
            dist = self.calculate(s, w, normalize)
            if (dist < best_dist and not normalize) or (dist > best_dist and normalize):
                best_dist = dist
                best_ind = i
        return best_ind, best_dist

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls._instances.get(cls) is None:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def set_ranges_between_refs(refs, section_ref):
    '''
    :refs: an unsorted list of segments such as [Ref(Rashi on Genesis 2:11), Ref(Rashi on Genesis 2:4), Ref(Rashi on Genesis 2:10)]
    where all refs have the same section
    :section_ref: the section reference for the list of refs, in this case Ref(Rashi on Genesis 2)
    :return: sorted list of ranged refs where the i-th element is a range from itself to the i+1-th element.
    The last ref in the list is a range from itself to the final segment in the section, which for Rashi on Genesis 2 is 25.
    In this case:
    [Ref(Rashi on Genesis 2:4-9), Ref(Rashi on Genesis 2:10), Ref(Rashi on Genesis 2:11-25)]
    If an empty list is passed as refs, we simply return a list with one range over the entire section, such as:
    [Ref(Rashi on Genesis 2:1-25)]
    '''
    if refs == []:
        first_ref = section_ref.subref(1)
        return [first_ref.to(section_ref.all_segment_refs()[-1])]


    ranged_refs = []
    len_list = len(refs)
    refs = sorted(refs, key=lambda x: x.order_id())
    last_ref = section_ref.all_segment_refs()[-1]
    #print "Refs: {}".format(refs)
    #print "Section: {}".format(section_ref)
    #print "Last ref: {}".format(last_ref)
    for i, ref in enumerate(refs):
        if ref.is_range():
            ranged_refs.append(ref)
            continue
        assert ref.section_ref() is section_ref
        if i + 1 == len_list:
            new_range = ref.to(last_ref)
        else:
            next_ref = refs[i+1]
            if next_ref.sections[-1] == ref.sections[-1]:
                ranged_refs.append(ref)
                continue
            else:
                d = next_ref._core_dict()
                d['sections'][-1] -= 1
                d['toSections'][-1] -= 1
                new_range = ref.to(Ref(_obj=d))
        ranged_refs.append(new_range)
    return ranged_refs


class PlaceHolder(object):
    """
    Useful for holding on to a variable without having to declare a name for them. Particulalrly useful for running a
    method and then using the result only if the method was successful.

    Example (uses re module)
    my_search = re.search(some_pattern, some_string)
    if my_search:
        print my_search.group()
    Becomes:
    holder = PlaceHolder()
    if holder(re.search(some_pattern, some_string)):
        print holder.group()

    """
    def __init__(self):
        self._obj_store = None

    def __call__(self, _obj):
        self._obj_store = _obj
        return _obj

    def __getattr__(self, item):
        return getattr(self._obj_store, item)

    def get_stored_item(self):
        return self._obj_store


def clean_whitespace(some_string):
    """
    Remove whitespace from beginning and end of string, as well as multiple spaces
    :param basestring some_string:
    :return:
    """
    return ' '.join(some_string.split())


def split_version(version_dict, num_splits):
    """
    Useful when a single version is larger than the max document size in mongodb (16MB). Breaks a version up, adding
    `Vol n`, where n = 1,2,3...<num_splits>.
    :param version_dict: Version dictionary, as would be uploaded to Sefaria without being split
    :param num_splits: Number of times to break up version (2 will give 2 version objects).
    :return: list of version objects
    """
    def edges(size):
        chunk_length = float(size) / float(num_splits)
        chunk_indices = [math.trunc(chunk_length * i) for i in range(num_splits + 1)]
        return list(zip(chunk_indices[:-1], chunk_indices[1:]))

    volumes = []
    indices = edges(len(version_dict['text']))
    for vol_num, (start, end) in enumerate(indices, 1):
        new_fields = {
            'versionTitle': '{}, Vol {}'.format(version_dict['versionTitle'], vol_num),
            'text': [t if start <= ind < end else [] for ind, t in enumerate(version_dict['text'])]
        }
        new_version = version_dict.copy()
        new_version.update(new_fields)
        volumes.append(new_version)
    return volumes


def split_list(list_to_split, num_splits):
    chunk_length = float(len(list_to_split)) / num_splits
    indices = [math.trunc(chunk_length * i) for i in range(num_splits + 1)]
    for start, end in zip(indices[:-1], indices[1:]):
        yield list_to_split[start:end]


def schema_with_default(simple_ja):
    """
    Take a standard JaggedArrayNode and makes it a default child of a SchemaNode.
    :param JaggedArrayNode simple_ja:
    :return: SchemaNode
    """
    root_node = SchemaNode()
    root_node.title_group = simple_ja.title_group
    root_node.key = simple_ja.key
    simple_ja.title_group = TitleGroup()
    simple_ja.key = "default"
    simple_ja.default = True
    root_node.append(simple_ja)
    root_node.validate()
    return root_node

def change_array(ja, callback):
    """
    Given a function(str) and a jagged array, returns a new jagged array after running the function on all elements.
    :param ja: a jagged array to be changed
    :param callback: a function run on substring
    :return: new jagged array with all elements changed by the functions
    """

    new_array = []

    for item in ja:

        if isinstance(item, list):
            new_array.append(change_array(item, callback))

        elif isinstance(item, str):
            new_array.append(callback(item))

        else:
            print('Jagged array contains unknown type')
            raise TypeError

    return new_array

def get_mapping_after_normalization(text, find_text_to_remove=None, removal_list=None, reverse=False):
    """
    Example.
        text = "a###b##c" find_text_to_remove = lambda x: [(m, '') for m in re.finditer(r'#+', x)]
        will return {1: 3, 2: 5}
        meaning by the 2nd index, 5 chars have been removed
        then if you have a range (0,3) in the normalized string "abc" you will know that maps to (0, 8) in the original string
    """
    if removal_list is None:
        removal_list = find_text_to_remove(text)
    total_removed = 0
    removal_map = {}
    for removal, subst in removal_list:
        try:
            start, end = removal
        except TypeError:
            # must be match object
            start, end = removal.start(), removal.end()
        normalized_text_index = start if reverse else (start + min(len(subst), end-start) - total_removed)
        total_removed += (end - start - len(subst))
        removal_map[normalized_text_index] = total_removed
    return removal_map

def convert_normalized_indices_to_unnormalized_indices(normalized_indices, removal_map, reverse=False):
    """
    normalized_indices is a list of tuples where each tuple is (x, y) x being start index, y is end index + 1
    """
    removal_keys = sorted(removal_map.keys())
    unnormalized_indices = []
    sign = -1 if reverse else 1
    for start, end in normalized_indices:
        unnorm_start_index = bisect_right(removal_keys, start) - 1
        unnorm_end_index = bisect_right(removal_keys, end) - 1

        unnorm_start = start if unnorm_start_index < 0 else start + (sign * removal_map[removal_keys[unnorm_start_index]])
        unnorm_end = end if unnorm_end_index < 0 else end + (sign * removal_map[removal_keys[unnorm_end_index]])
        unnormalized_indices += [(unnorm_start, unnorm_end)]
    return unnormalized_indices


def char_indices_from_word_indices(input_string, word_ranges, split_regex=None):
    """
    ***Important***
    We use regular expression matching to solve this problem. We use the regex \s+ as default. This *should* replicate
    the behavior of str.split(), but use this with caution. It would be advisable to send the exact regex that was used
    to split the string in the first place.

    :param input_string: Original string that was split into a word list

    :param word_ranges: list of tuples, where each tuple represents a range of words from the word list.
    (first_word, last_word) where last_word is the actual index of the last word
    (the range of words would be word_list[first_word:last_word+1]).
    This matches the results returned from dibbur_hamtchil_matcher.match_text

    :param split_regex: Regular expression pattern to split. If none is supplied will use r'\s+'. see note above.
    :return:
    """

    if not split_regex:
        split_regex = r'\s+'
    regex = re.compile(split_regex)
    split_words = regex.split(input_string)
    count, word_indices = 0, []
    for word in split_words:
        start = count
        count += len(word)
        end = count
        word_indices.append((start, end))
    removal_map = get_mapping_after_normalization(input_string, lambda x: [(m, '') for m in regex.finditer(x)])
    normalized_char_indices = []
    for i, words in enumerate(word_ranges):
        first_word, last_word = [w if w < len(word_indices) else -1 for w in words]
        normalized_char_indices.append(
            (
                word_indices[first_word][0] if first_word >=0 else -1,
                word_indices[last_word][1] if last_word >= 0 else -1
            )
        )
    return convert_normalized_indices_to_unnormalized_indices(normalized_char_indices, removal_map)


@lru_cache(maxsize=32)
def get_word_indices(input_string, split_regex=r'\s+'):
    """
    helper method for word_index_from_char_index. Broken out for memoization purposes
    """
    return [r.end() for r in re.finditer(split_regex, input_string)]


def word_index_from_char_index(full_string, char_index, split_regex=r'\s+'):
    word_indices = get_word_indices(full_string, split_regex)
    return bisect_right(word_indices, char_index) if char_index >= 0 else -1


def sanitized_words_to_unsanitized_words(input_string, sanitized_string, sanitization_method, sanitized_word_ranges):
    removal_map = get_mapping_after_normalization(input_string, sanitization_method)
    sanitized_char_ranges = char_indices_from_word_indices(sanitized_string, sanitized_word_ranges)
    unsanitzied_char_ranges = convert_normalized_indices_to_unnormalized_indices(sanitized_char_ranges, removal_map)
    # for char_range in unsanitied_char_ranges:
    #     word_range = tuple(word_index_from_char_index(input_string, i) for i in char_range)
    #     stuff.append(word_range)
    return [tuple(word_index_from_char_index(input_string, i) for i in char_range)
            for char_range in unsanitzied_char_ranges]


class TextSanitizer:
    """
    This class is designed so we can easily move from a list of segments to the flat list of words necessary
    for use in dibbur_hamatchil_matcher.match_text. It is primarily helpful when we need to keep track of text before and after edits were
    made to said text that were necessary for improving text matching.
    """
    def __init__(self, section: List[str], divider_pattern: str):
        self._original_segments = tuple(section)
        self._sanitized_segments = None
        self.sanitizer = None
        self._dividing_expression = divider_pattern

        # these variables hold the indices of the first word for each segment
        self._sanitzed_word_indices = None
        self._unsanitized_word_indices = None
        self._set_unsanitzed_word_indices()

    def get_original_segments(self):
        return self._original_segments

    def set_sanitizer(self, sanitizer: Callable[[str], str]):
        self.sanitizer = sanitizer

    def sanitize(self):
        if not self.sanitizer:
            raise AttributeError("no sanitization method set for this instance")
        self._sanitized_segments = tuple(self.sanitizer(x) for x in self._original_segments)
        self._set_sanitized_word_indices()

    def get_sanitized_segments(self):
        if self.sanitizer and not self._sanitized_segments:
            self.sanitize()
        return self._sanitized_segments

    def _set_unsanitzed_word_indices(self):
        self._unsanitized_word_indices = self.get_segment_start_indices(
            self._original_segments, self._dividing_expression)

    def _set_sanitized_word_indices(self):
        self._sanitzed_word_indices = self.get_segment_start_indices(
            self._sanitized_segments, self._dividing_expression
        )

    def get_unsanitized_word_indices(self):
        return tuple(self._unsanitized_word_indices)

    def get_sanitized_word_indices(self):
        if self._sanitzed_word_indices:
            return tuple(self._sanitzed_word_indices)
        elif self.sanitizer:
            self.sanitize()
            return tuple(self._sanitzed_word_indices)
        else:
            raise AttributeError('Cannot get sanitied word indices: No sanitizer set')

    def set_dividing_expression(self, regex_pattern: str):
        self._dividing_expression = regex_pattern

    @staticmethod
    def make_word_list(section, dividing_expression):
        word_list = []
        for segment in section:
            segment_list = re.split(dividing_expression, segment)
            word_list.extend(segment_list)
        return word_list

    def get_sanitized_word_list(self):
        if not self._sanitized_segments:
            if self.sanitizer:
                self.sanitize()
            else:
                raise AttributeError("Sanitizer not set")
        return self.make_word_list(self._sanitized_segments, self._dividing_expression)

    def get_unsanitized_word_list(self):
        return self.make_word_list(self._original_segments, self._dividing_expression)

    @staticmethod
    def get_segment_start_indices(segment_list, divider_pattern):
        """
        Calculates the word number at which each segment starts. Helpful if trying to move from a flat list of words
        back to a segment division.
        :param segment_list:
        :param divider_pattern:
        :return:
        """
        segment_start_indices = []
        word_count = 0
        for segment in segment_list:
            segment_start_indices.append(word_count)
            word_count += len(re.split(divider_pattern, segment))

        return segment_start_indices

    @staticmethod
    def get_segment_index_from_word_index(word_index, start_segment_list):
        return bisect_right(start_segment_list, word_index) - 1

    def check_sanitized_index(self, word_index: int):
        """
        given a word index from a sanitized word list, find what segment it originated from
        """
        return self.get_segment_index_from_word_index(word_index, self._sanitzed_word_indices)

    def check_unsanitized_word_index(self, word_index:int):
        return self.get_segment_index_from_word_index(word_index, self._unsanitized_word_indices)
def get_window_around_match(start_char:int, end_char:int, text:str, window:int=10) -> tuple:
    before_window, after_window = '', ''

    before_text = text[:start_char]
    before_window_words = list(filter(lambda x: len(x) > 0, before_text.split()))[-window:]
    before_window = " ".join(before_window_words)

    after_text = text[end_char:]
    after_window_words = list(filter(lambda x: len(x) > 0, after_text.split()))[:window]
    after_window = " ".join(after_window_words)

    return before_window, after_window

def is_abbr_of(abbr, unabbr, match=lambda x, y: x.startswith(y), lang='he'):
    abbr = re.sub('[^א-ת]', '', abbr) if lang == 'he' else re.sub('[^a-z]', '', abbr)
    unabbr = unabbr.split()
    indexes = [[index for index, letter in enumerate(abbr) if word[0] == letter] for w, word in enumerate(unabbr)]
    choices = itertools.product(*indexes)
    for choi in choices:
        if choi[0] == 0 and all(i < j for i, j in zip(choi, choi[1:])):
            choi += (None,)
            if all(match(unabbr[n], abbr[choi[n]:choi[n+1]]) for n in range(len(unabbr))):
                return True
    return False
