# -*- coding: utf-8 -*-
import codecs
from sefaria.datatype import jagged_array
import re
from data_utilities.util import jagged_array_to_file as j_to_file


def file_to_ja(structure, infile, expressions, cleaner):
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
    regexes, indices = [re.compile(ex) for ex in expressions], [-1 for ex in expressions]
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


def align_comments(text_array):
    # strip out unnecessary lines
    remove = re.compile(u'@99')
    for index, line in enumerate(text_array):
        if remove.search(line):
            del text_array[index]

    result, tmp = [], []
    t = u''.join(text_array)
    t = t.replace(u'\n', u'')
    t = t.replace(u'\r', u'')
    t = t.split(u' ')
    for word in t:
        if re.search(u'@11[\u05d0-\u05ea"]{1,4}\)', word):
            if tmp:
                result.append(re.sub(u'@[0-9]{2}', u'', u' '.join(tmp)))
            tmp = []
        else:
            tmp.append(word)

    else:
        result.append(re.sub(u'@[0-9]{2}', u'', u' '.join(tmp)))
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
