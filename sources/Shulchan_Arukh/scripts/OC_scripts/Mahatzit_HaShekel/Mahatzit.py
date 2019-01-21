# encoding=utf-8

"""
vol. 2 starts at 242
vol. 3 starts at 417

Parsing strategy for Seifim:
Search for:
סק <סעיף>
at the beginning of of a line. Filter out punctuation, parentheses and @ marks. A space does not have to appear between
the סק and the Seif. Anything that is not marked at the beginning becomes part of Seif א.

Parsing strategy for Comments:
Here we need to take different strategies for vol. 1 and volumes 2 & 3. Vol. 1 is already split reasonably well. 2 & 3
need to be split. For that, we'll start with splitting on ":" characters.

Formatting:
We'll want to strip out all @ marks. We want to mark dh by looking ahead for כו or a period, but only in the first
several words. This heuristic could be an alternative comment parsing strategy for the comments of vol. 2 & 3.
"""

import re
import codecs
from functools import partial
from data_utilities.util import getGematria, convert_dict_to_array
from data_utilities.ParseUtil import Description, directed_run_on_list, ParsedDocument, ParseState, ClashError


chap_regex = re.compile(u"^@22(\u05e1\u05d9\u05de\u05df|\u05e1\u05d9'?)\s(?P<chap>[\u05d0-\u05ea\"]{1,5})$")

with codecs.open('Mahatzit.txt', 'r', 'utf-8') as fp:
    lines = fp.readlines()


def get_chap_values():
    for line in lines:
        match = chap_regex.match(line)
        if match:
            yield getGematria(match.group('chap'))


def split_chaps():
    """
    Returns a function
    :return:
    """
    def resolver(text_line):
        match = chap_regex.match(text_line)
        if match:
            return getGematria(match.group('chap'))
        else:
            return False
    return directed_run_on_list(resolver, include_matches=False, one_indexed=True)


def split_seifim(parsing_state, comments):
    """
    just make a dict of lists. Just start appending to the list. Special case first seif.

    Point the dict to an updating list. If a seif gets hit twice raise a ClashError, unless this is Seif א.
    Use the ParseState to help with reporting in case of a clash
    :param comments:
    :return:
    """
    pass
