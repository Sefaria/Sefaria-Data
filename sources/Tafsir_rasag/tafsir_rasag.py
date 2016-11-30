# encoding=utf-8

import re
import os
import codecs
from collections import OrderedDict
from data_utilities.util import ja_to_xml, traverse_ja
from sources import functions
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
                print 'problem at {}: Should be {}, found {}'.format(old, len(old.all_subrefs()), len(new))


def build_links(parsed_data):

    link_bases = []

    for book in library.get_indexes_in_category('Torah'):
        for segment in traverse_ja(parsed_data[book]):
            link_bases.append('{} {}:{}'.format(book, *[i+1 for i in segment['indices']]))

    return [{
        'refs': [base, 'Tafsir Rasag, {}'.format(base)],
        'type': 'targum',
        'auto': False,
        'generated_by': 'Tafsir Rasag Parse script'
    } for base in link_bases]


def build_index():

    root = SchemaNode()
    root.add_title('Tafsir Rasag', 'en', primary=True)
    root.add_title(u'תפסיר רס"ג', 'he', primary=True)
    root.key = 'Tafsir Rasag'
    root.add_title('Tafsir Torah', 'en')
    root.add_title(u'תפסיר תורה', 'he')
    root.add_title('Tafsir Rasag Arabic Translation to Torah', 'en')

    intro_node = JaggedArrayNode()
    intro_node.add_title('Introduction', 'en', primary=True)
    intro_node.add_title(u'הקדמה', 'he', primary=True)
    intro_node.key = 'Introduction'
    intro_node.depth = 1
    intro_node.addressTypes = ['Integer']
    intro_node.sectionNames = ['Paragraph']
    root.append(intro_node)

    for book in library.get_indexes_in_category('Torah'):
        book_node = JaggedArrayNode()
        book_node.add_title(book, 'en', primary=True)
        book_node.add_title(Ref(book).he_book(), 'he', primary=True)
        book_node.key = book
        book_node.depth = 2
        book_node.addressTypes = ['Integer', 'Integer']
        book_node.sectionNames = ['Chapter', 'Verse']
        root.append(book_node)
    root.validate()

    return {
        'title': 'Tafsir Rasag',
        'categories': ['Tanakh', 'Targum'],
        'schema': root.serialize()
    }


def post():
    books = file_to_books()
    for book in library.get_indexes_in_category('Torah'):
        books[book] = align_text(books[book], u'@\u05e4\u05e8\u05e7 [\u05d0-\u05ea]{1,2}', u'[0-9]{1,2}\.')

    functions.post_index(build_index())
    node_names = ['Introduction'] + library.get_indexes_in_category('Torah')
    for name in node_names:
        version = {
            'versionTitle': 'Tafsir al-Torah bi-al-Arabiya, Paris, 1893',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001863864',
            'language': 'he',
            'text': books[name]
        }
        functions.post_text('Tafsir Rasag, {}'.format(name), version)

    functions.post_link(build_links(books))


post()
