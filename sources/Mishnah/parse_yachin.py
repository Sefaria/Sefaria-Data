# -*- coding: utf-8 -*-
import codecs
from sefaria.datatype import jagged_array
import re
from data_utilities.util import jagged_array_to_file as j_to_file, getGematria
from data_utilities.sanity_checks import *
from sources import functions
from sefaria.model import *


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
                indices[i+1:] = [0 for x in indices[i+1:]]
                break

        else:
            if indices.count(-1) == 0:
                temp.append(line)
    else:
        ja.set_element(indices, cleaner(temp))

    return ja


def get_file_names(category):
    """
    Get a list of all the file names for specified category
    :param category: משניות, יכין, בועז
    :return: List of all filenames in specified category
    """

    tractates = library.get_indexes_in_category('Mishnah')
    file_names = []

    for book in tractates:

        he_name = Ref(book).he_book()
        he_name = he_name.replace(u'משנה', category)
        file_names.append(u'{}.txt'.format(he_name))

    return file_names


def do_nothing(text_array):
    return text_array


def simple_align(text):

    clean = []

    for line in text:
        line = line.replace(u'\n', u'')
        line = line.replace(u'\r', u'')

        if line != u'':
            clean.append(line)

    return clean


def boaz_align(text):

    clean = []
    reg = re.compile(u'@22')

    for line in text:
        line = line.replace(u'\n', u'')
        line = line.replace(u'\r', u'')

        if reg.match(line):
            clean.append(line)
        else:
            clean[-1] += line

    return clean


def align_comments(text_array):
    # strip out unnecessary lines
    remove = re.compile(u'@99')
    for index, line in enumerate(text_array):
        if remove.search(line):
            del text_array[index]

    section_name, result, tmp = '', {}, []
    t = u''.join(text_array)
    t = t.replace(u'\n', u'')
    t = t.replace(u'\r', u'')
    t = t.split(u' ')
    for word in t:
        search = re.search(u'@11([\u05d0-\u05ea"]){1,4}\*?\)', word)
        if search:
            section_name = getGematria(search.group(1).replace(u'"', u''))
            if section_name in result.keys():
                result[section_name].append(u'\n')
        if section_name not in result.keys():
            result[section_name] = []

        result[section_name].append(re.sub(u'@[0-9]{2}', u'', word))

    return result


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


def grab_intro(infile, stop_tag, cleaner=None):
    """
    An introduction lies outside the regular chapter verse structure of the text. Use this function to grab the
    intro
    :param infile: input file to read from.
    :param stop_tag: When this pattern is recognized, the function will return
    :param cleaner: A function that takes a list of strings and returns a list of strings
    :return: List of string(s).
    """

    stop_tag = re.compile(stop_tag)

    result = []

    for line in infile:

        if stop_tag.search(line):
            if cleaner:
                return cleaner(result)
            else:
                return result
        else:
            result.append(line)

    else:
        infile.close()
        raise EOFError('Hit the end of the file')


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


def find_boaz_in_yachin(yachin_struct, boaz_struct, comment_tag):
    """
    Check that yachin has all the links to boaz. First take a parsed boaz, check how many comments are in a given
    chapter, then see if the corresponding yachin structure has tags that can be linked to said boaz.
    :param yachin_struct: A roughly parsed ja-like structure of Yachin - depth 2
    :param boaz_struct: Same as above, but for boaz.
    :param comment_tag: syntax for regular expression with which to find tags in Yachin
    :return: Dictionary 'chapter': diff (int representing the difference in comments between commentaries)
    """

    comment_reg = re.compile(comment_tag)
    diffs = []

    # loop through boaz
    for index, section in enumerate(boaz_struct):

        try:
            # count number of comments in chapter of boaz
            num_comments = len(section)

            # grab Yachin chapter
            y_chapter = u' '.join(yachin_struct[index])

            # number of boaz references in Yachin chapter
            b_comments_in_y = len(comment_reg.findall(y_chapter))

            diffs.append(b_comments_in_y - num_comments)

        except IndexError:

            diffs.append(-999)

    return diffs


def parse_boaz(input_file):

    expression = u'@00(?:\u05e4\u05e8\u05e7 |\u05e4")([\u05d0-\u05ea"]{1,3})'

    simple_parse = file_to_ja([[]], input_file, [expression], boaz_align)

    # reset file
    input_file.seek(0)

    headers = [functions.getGematria(x) for x in grab_section_names(expression, input_file, 1)]

    comp_parse = simple_to_complex(headers, simple_parse.array())

    full_parse = functions.convertDictToArray(comp_parse)

    return full_parse


def yachin_boaz_diffs(output_file):
    """
    Simple parse of Yachin and Boaz, run find_boaz_in_yachin, then print diffs if necessary
    """

    tractates = library.get_indexes_in_category('Mishnah')
    count = 0

    for book in tractates:

        he_name = Ref(book).he_book()


        try:
            yachin_file = codecs.open(u'{}.txt'.format(he_name.replace(u'משנה', u'יכין')), 'r', 'utf-8')
            boaz_file = codecs.open(u'{}.txt'.format(he_name.replace(u'משנה', u'בועז')), 'r', 'utf-8')
        except IOError:
            continue

        y_jarray = file_to_ja([[]], yachin_file, [u'@00(?:\u05e4\u05e8\u05e7 |\u05e4)([\u05d0-\u05ea"]{1,3})'],
                              simple_align, True)
        b_array = parse_boaz(boaz_file)

        diffs = find_boaz_in_yachin(y_jarray.array(), b_array, u'@22')

        yachin_file.close()
        boaz_file.close()

        for index, value in enumerate(diffs):

            if value > 0:
                count += 1
                output_file.write(u'{}: {} extra comment(s) found in {} chapter {}\n'
                                  .format(count, abs(value), book.replace(u'Mishnah', u'Yachin'), index + 1))

            elif value < 0 and value != -999:
                count += 1
                output_file.write(u'{}: {} extra comment(s) found in {} chapter {}\n'
                                  .format(count, abs(value), book.replace(u'Mishnah', u'Boaz'), index + 1))

            elif value == -999:
                count += 1
                output_file.write(u'{} strange issue at {} chapter {}\n'.format(count, book, index+1))


def double_tags():

    chap_reg = u'@00(?:\u05e4\u05e8\u05e7 |\u05e4")([\u05d0-\u05ea"]{1,3})'
    boaz_reg = u'@44\([\u05d0-\u05ea"]{1,3}'

    for text_file in get_file_names(u'משניות'):

        input_file = codecs.open(text_file, 'r', 'utf-8')

        double_tags = find_double_tags(chap_reg, boaz_reg, input_file)

        if double_tags:

            print u'{}: {}'.format(text_file, double_tags)


def yachin_builder(text_list):
    """
    Takes a raw list of yachin comments in a chapter and parses them into the correct structure.
    Does not remove links and other garbage that might exist in the text.
    :param text_list: A list of strings
    :return: Nested list of strings (unicode)
    """

    chapter = []

    new_comment = re.compile(u'@11[\u05d0-\u05ea"]{1,3}\)')

    for line in text_list:

        # if nothing has been added to chapter, this is clearly the start of something new - append
        if not chapter:
            chapter.append([line])

        # tagged lines get added as a new list
        elif new_comment.search(line):
            chapter.append([line])

        # lines that don't match the tag get added to the last entry
        else:
            chapter[-1].append(line)

    return chapter

a = codecs.open(u'יכין כלים.txt', 'r', 'utf-8')
b = codecs.open('yachintest.txt', 'w', 'utf-8')
ja = file_to_ja([[]], a, [u'@00(?:\u05e4\u05e8\u05e7 |\u05e4)([\u05d0-\u05ea"]{1,3})'], yachin_builder)
j_to_file(b, ja.array(), [u'chapter', u'comment group', u'comment'])
a.close()
b.close()
