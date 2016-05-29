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


infile = codecs.open('יכין עדיות.txt', 'r', 'utf-8')
j = file_to_ja([[]], infile, [u'@00פרק'], align_comments)
infile.close()
outfile = codecs.open('yachin_test.txt', 'w', 'utf-8')
j_to_file(outfile, j.array(), ['perek', 'comment'])
outfile.close()