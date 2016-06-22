# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import os
import sys
import re
import codecs
from sefaria.datatype import jagged_array
from sources.local_settings import *
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


def file_to_ja(structure, infile, expressions, cleaner, grab_all=False):
    """
    Designed to be the first stage of a reusable parsing tool. Adds lines of text to the Jagged
    Array in the desired structure (Chapter, verse, etc.)
    :param structure: A nested list one level lower than the final result. Example: for a depth 2
    text, structure should be [[]].
    :param infile: Text file to read from
    :param expressions: A list of regular expressions with which to identify segment (chapter) level. Do
    not include an expression with which to break up the actual text.
    :param cleaner: A function that takes a list of strings and returns an array with the text broken up
    correctly. Should also break up and remove unnecessary tagging data.
    :param grab_all: If set to true, will grab the lines indicating new sections.
    :return: A jagged_array with the text properly structured.
    """

    # instantiate ja
    ja = jagged_array.JaggedArray(structure)

    if structure == []:
        depth = 1
    else:
        depth = ja.get_depth()

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
            clean_array.append(re.sub(u' +', u' ', item))

        else:
            print 'Jagged array contains unknown type'
            raise TypeError

    return clean_array


def traverse_ja(ja, indices=[], bottom=unicode):
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

    if type(ja) is bottom:
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
    updated = codecs.open('{}.tmp'.format(filename), 'w', 'utf-8')

    for line in original:
        new_line = function(line, *args)
        updated.write(new_line)

    original.close()
    updated.close()

    os.remove(filename)
    os.rename('{}.tmp'.format(filename), filename)