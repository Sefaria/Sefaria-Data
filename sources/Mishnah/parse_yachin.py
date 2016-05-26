# -*- coding: utf-8 -*-
from sefaria.datatype import jagged_array
import re


def file_to_ja(structure, infile, expressions, cleaner):
    """
    Designed to be the first stage of a reusable parsing tool. Adds lines of text to the Jagged Array
    in the desired structure (Chapter, verse, etc.)
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
        matches = [reg.search(line) for reg in regexes]
