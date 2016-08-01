# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util



perek_number = regex.compile(u'\u05e4\u05e8\u05e7\s([\u05d0-\u05ea]{1,2})')
pasuk_number = regex.compile(u'([\u05d0-\u05ea]{1,2})\s')

all_of_humash, book, chapter = [], [], []
last_chapter, last_pasuk = 1, 0
first_book, new_book, new_chapter = True, True, True
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

                    match_object = perek_number.search(each_line)
                    current_chapter = util.getGematria(match_object.group(1))
                    diff = current_chapter - last_chapter
                    while diff > 1:
                        book.append([])
                        diff -= 1
                    last_chapter = current_chapter
                    new_chapter = True
                    last_pasuk = 0

                else:
                    new_book = False
                    new_chapter = True
                    last_pasuk = 0

            else:
                match_object = pasuk_number.search(each_line)
                current_pasuk = util.getGematria(match_object.group(1))
                diff = current_pasuk - last_pasuk
                while diff > 1:
                    chapter.append('')
                    diff -= 1
                last_pasuk = current_pasuk
                each_line = each_line.replace(match_object.group(), '')
                chapter.append(each_line)



    book.append(chapter)
    all_of_humash.append(book)


testing_file = codecs.open("testing_file.txt", 'w', 'utf-8')
util.jagged_array_to_file(testing_file, all_of_humash, ['Book', 'Chapter', 'Verse'])
testing_file.close()
