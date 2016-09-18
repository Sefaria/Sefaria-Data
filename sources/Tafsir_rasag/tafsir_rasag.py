# encoding=utf-8

import re
import codecs
from collections import OrderedDict
from data_utilities.util import ja_to_xml
from sefaria.model import *


def file_to_books():
    node_names = ['Introduction'] + library.get_indexes_in_category('Torah')
    node_text = OrderedDict([(name, []) for name in node_names])
    node_reg = re.compile(u'^ספר')
    names = iter(node_names)

    with codecs.open('tafsir_torah.txt', 'r', 'utf-8') as infile:
        lines = infile.readlines()

    container = node_text[next(names)]
    for line in lines:
        if node_reg.search(line):
            container = node_text[next(names)]
        else:
            container.append(line)

    return node_text


def align_text(text_list, chap_reg, verse_reg):
    """
    Take a list of strings which are broken up arbitrarily and realign them into a list with some structure
    :param text_list: list of strings
    :param chap_reg: regular expressions to identify chapters
    :param verse_reg: regular expression to identify verses
    :return:
    """
    assert isinstance(text_list, list)

    combined = re.sub(u' +', u' ', u' '.join(text_list))
    combined = re.sub(u'\n', u'', combined)
    skip = lambda x: None if x == u'' or re.sub(u' +', u' ',  x) == u' ' else x
    just_chaps = filter(skip, re.split(chap_reg, combined))  # we're just chaps, not very close
    with_verses = [filter(skip, re.split(verse_reg, chapter)) for chapter in just_chaps]

    return with_verses


def sanity_check(parsed):
    """
    Check that each book has the correct number of chapters and verses
    :param parsed: parsed text dictionary
    """
    for book in library.get_indexes_in_category('Torah'):

        chapters = Ref(book).all_subrefs()
        if len(chapters) == len(parsed[book]):
            print '{} has the correct number of chapters'.format(book)
        else:
            print 'wrong number of chapters in {}'.format(book)
        chapters = zip(chapters, parsed[book])

        for old, new in chapters:
            if len(old.all_subrefs()) == len(new):
                continue
            else:
                print 'problem at {}'.format(old)

books = file_to_books()
for book in library.get_indexes_in_category('Torah'):
    books[book] = align_text(books[book], u'@\u05e4\u05e8\u05e7 [\u05d0-\u05ea]{1,2}', u'[0-9]{1,2}\.')
sanity_check(books)
