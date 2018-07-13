# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
from sources.Targum_Pseudo_Jonathan_in_English import tsj_functions

english_book_names = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']

all_five_books = tsj_functions.parse_targum_pseudo_jonathan()

for book, book_name in zip(all_five_books, english_book_names):
    print(book_name)
    ref = 'Targum Jonathan on {}'.format(book_name)
    text = tsj_functions.create_text(book)
    functions.post_text(ref, text)

testing_file = codecs.open("testing_file.txt", 'w', 'utf-8')
util.jagged_array_to_file(testing_file, all_five_books, ['Book', 'Chapter', 'Verse'])
testing_file.close()
