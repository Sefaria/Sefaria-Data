# encoding=utf-8

"""
vol. 2 starts at 242
vol. 3 starts at 417
"""

import re
import codecs
from data_utilities.util import getGematria
from data_utilities.ParseUtil import Description, directed_run_on_list, ParsedDocument


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
