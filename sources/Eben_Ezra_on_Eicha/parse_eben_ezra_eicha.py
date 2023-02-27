# -*- coding: utf-8 -*-
import codecs
from sefaria.model import *
import regex
from sources import functions
from parsing_utilities import util
from sources.Eben_Ezra_on_Eicha import eee_functions

"""
index record
parse text
text record
link
clean
"""

index = eee_functions.create_index()
functions.post_index(index)

eben_ezra = eee_functions.parse()

for index, each_text in enumerate(eben_ezra):
    ref = 'Eben Ezra on Lamentations'
    if index == 0:
        ref = 'Eben Ezra on Lamentations,_Introduction'
    text = eee_functions.create_text(each_text)
    functions.post_text(ref, text)


list_of_links = eee_functions.create_links(eben_ezra[1])
functions.post_link(list_of_links)

testing_file = codecs.open("testing_file.txt", 'w', 'utf-8')
util.jagged_array_to_file(testing_file, eben_ezra, ["AHHHHH", 'PEREK', 'MISHNA', 'COMMENT'])
testing_file.close()
