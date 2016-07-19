# -*- coding: utf-8 -*-
from data_utilities import util
import sys
import codecs
import re
from sefaria.model import *

"""
Parsing strategy: Use @00 and @22 for structure in the auto-parser.

Two places have a repeated numbered comment (i.e. a and a*). I think dropping to depth 3 is silly, I'll add a line
break instead.
"""


def get_file_names():

    he = [Ref(book).he_book() for book in library.get_indexes_in_category('Mishnah')[:-5]]
    boaz_file_names = [u'{}.txt'.format(name.replace(u'משנה', u'בועז')) for name in he]
    return boaz_file_names


def files_with_tag(tag):
    files = []
    for filename in get_file_names():
        with codecs.open(filename, 'r', 'utf-8') as boaz_file:
            for line in boaz_file:
                if re.search(tag, line):
                    files.append(filename)
                    break
    print 'found {} files with tag {}'.format(len(files), tag)
    for thing in files:
        print thing


def find_strange_stuff():
    weird_chars = []
    for filename in get_file_names():
        with codecs.open(filename, 'r', 'utf-8') as boaz_file:
            for line in boaz_file:
                weird_chars.append(re.findall(u'[^\u05d0-\u05ea \.0-9\(\):@\[\"]', line))
    weird_chars = [thing for char_list in weird_chars for thing in char_list]
    return set(weird_chars)


