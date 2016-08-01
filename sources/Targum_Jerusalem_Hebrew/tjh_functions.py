# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util


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
                        last_chapter = fill_in_missing_sections_and_updated_last(each_line, book, perek_number, [], last_chapter)
                    else:
                        new_book = False
                    last_pasuk = 0

                else:
                    last_pasuk = fill_in_missing_sections_and_updated_last(each_line, chapter, pasuk_number, '', last_pasuk)
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


