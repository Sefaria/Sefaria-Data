# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util


def parse_targum_isaiah_english():
    book_chapter_verse = regex.compile('(Isa)\s(\d{1,2}):(\d{1,2})')
    book, chapter = [], []
    last_chapter = '1'

    with codecs.open('targum_isaiah.txt', 'r', 'utf-8') as the_file:
        for each_line in the_file:
            match_object = book_chapter_verse.search(each_line)
            if match_object:
                each_line = each_line.replace(match_object.group(0), '')
                if match_object.group(2) != last_chapter:
                    book.append(chapter)
                    chapter = [each_line]
                    last_chapter = match_object.group(2)

                else:
                    chapter.append(each_line)

    book.append(chapter)
    return book


def create_text(text):
    return {
        "versionTitle": "",
        "versionSource": "",
        "language": "en",
        "text": text
    }
