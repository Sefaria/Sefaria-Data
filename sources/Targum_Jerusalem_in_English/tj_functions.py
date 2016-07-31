# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode
from fuzzywuzzy import fuzz
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys


def parse_targum_jerusalem_english():
    book_chapter_verse = regex.compile('(Gen|Exo|Lev|Num|Deu)\s(\d{1,2}):(\d{1,2})')
    all_of_chumash, book, chapter = [], [], []
    last_book, last_chapter = 'Gen', '1'

    with codecs.open('targum_jerusalem_english.txt', 'r', 'utf-8') as the_file:
        for each_line in the_file:
            match_object = book_chapter_verse.search(each_line)
            each_line = each_line.replace(match_object.group(0), '')

            if match_object.group(1) != last_book:
                book.append(chapter)
                all_of_chumash.append(book)
                book, chapter = [], [each_line]
                last_book, last_chapter = match_object.group(1), match_object.group(2)

            elif match_object.group(2) != last_chapter:
                trial = match_object.group(2)
                book.append(chapter)
                chapter = [each_line]
                last_chapter = match_object.group(2)

            else:
                chapter.append(each_line)

    book.append(chapter)
    all_of_chumash.append(book)
    return all_of_chumash







