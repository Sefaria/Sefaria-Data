# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode


def parse():
    perek_number = regex.compile(u'\u05e4\u05e8\u05e7\s([\u05d0-\u05ea]{1,2})')
    pasuk_number = regex.compile(u'([\u05d0-\u05ea]{1,2})\s')

    all_of_humash, book, chapter = [], [], []
    last_chapter, last_pasuk = 1, 0
    first_book, new_book = True, True

    with codecs.open('targum_jerusalem_hebrew.txt', 'r', 'utf-8') as the_file:
        for each_line in the_file:
            each_line = each_line.strip()
            if each_line:
                if "@00" in each_line:
                    if not first_book:
                        book.append(chapter)
                        all_of_humash.append(book)
                        book, chapter = [], []
                        new_book = True
                        last_chapter = 1
                    else:
                        first_book = False

                elif "@01" in each_line:
                    if not new_book:
                        book.append(chapter)
                        chapter = []
                        last_chapter = fill_in_missing_sections_and_updated_last(each_line, book, perek_number, [],
                                                                                 last_chapter)
                    else:
                        new_book = False
                    last_pasuk = 0

                else:
                    last_pasuk = fill_in_missing_sections_and_updated_last(each_line, chapter, pasuk_number, '',
                                                                           last_pasuk)
                    each_line = clean_up(each_line, pasuk_number)
                    chapter.append(each_line)

        book.append(chapter)
        all_of_humash.append(book)
        return all_of_humash


def fill_in_missing_sections_and_updated_last(each_line, base_list, this_regex, filler, last_index):
    match_object = this_regex.search(each_line)
    current_index = util.getGematria(match_object.group(1))
    diff = current_index - last_index
    while diff > 1:
        base_list.append(filler)
        diff -= 1
    return current_index


def clean_up(string, this_regex):
    match_object = this_regex.search(string)
    string = string.replace(match_object.group(1), '')
    return string.strip()


def create_index_record():
    the_schema = create_the_schema()
    the_schema.validate()
    index = {
        "title": "Targum Jerusalem",
        "categories": ["Tanakh", "Targum"],
        "schema": the_schema.serialize()
    }
    return index


def create_the_schema():
    english_names = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    hebrew_names = [u'בראשית', u'שמות', u'ויקרא', u'במדבר', u'דברים']
    targum_jerusalem = SchemaNode()
    targum_jerusalem.add_title('Targum Jerusalem', 'en', primary=True)
    targum_jerusalem.add_title(u'תרגום ירושלמי', 'he', primary=True)
    targum_jerusalem.key = 'Targum Jerusalem'
    for english_name, hebrew_name in zip(english_names, hebrew_names):
        targum_jerusalem.append(create_jagged_array_nodes(english_name, hebrew_name))
    return targum_jerusalem


def create_jagged_array_nodes(en_name, he_name):
    book_node = JaggedArrayNode()
    book_node.key = en_name
    book_node.add_title(en_name, 'en', primary=True)
    book_node.add_title(he_name, 'he', primary=True)
    book_node.depth = 2
    book_node.addressTypes = ["Integer", "Integer"]
    book_node.sectionNames = ["Chapter", "Verse"]
    return book_node


def create_text(ja):
    return {
        "versionTitle": "Targum Jerusalem on Torah",
        "versionSource": "https://he.wikisource.org/wiki/%D7%AA%D7%A8%D7%92%D7%95%D7%9D_%D7%99%D7%A8%D7%95%D7%A9%D7%9C%D7%9E%D7%99_(%D7%A7%D7%98%D7%A2%D7%99%D7%9D)_%D7%9C%D7%AA%D7%95%D7%A8%D7%94",
        "language": "he",
        "text": ja
    }
