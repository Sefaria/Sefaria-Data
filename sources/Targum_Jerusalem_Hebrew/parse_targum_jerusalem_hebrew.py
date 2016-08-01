# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
from sources.Targum_Jerusalem_Hebrew import tjh_functions

english_names = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
index = tjh_functions.create_index_record()
functions.post_index(index)

all_of_humash = tjh_functions.parse()

for book, book_name in zip(all_of_humash, english_names):
    ref = 'Targum Jerusalem, {}'.format(book_name)
    text = tjh_functions.create_text(book)
    functions.post_text(ref, text)

list_of_links = tjh_functions.create_links(all_of_humash)
functions.post_link(list_of_links)

testing_file = codecs.open("testing_file.txt", 'w', 'utf-8')
util.jagged_array_to_file(testing_file, all_of_humash, ['Book', 'Chapter', 'Verse'])
testing_file.close()
