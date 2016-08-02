# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
from sources.Targum_Jerusalem_English import tje_functions

english_book_names = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']

all_five_books = tje_functions.parse_targum_jerusalem_english()

# for book, book_name in zip(all_five_books, english_book_names):
#     print(book_name)
#     ref = 'Targum Jonathan on {}'.format(book_name)
#     text = tje_functions.create_text(book)
#     functions.post_text(ref, text)

testing_file = codecs.open("testing_file.txt", 'w', 'utf-8')
util.jagged_array_to_file(testing_file, all_five_books, ['Book', 'Chapter', 'Verse'])
testing_file.close()
