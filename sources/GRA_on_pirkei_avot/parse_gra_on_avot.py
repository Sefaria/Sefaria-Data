# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
from sources.GRA_on_pirkei_avot import gra_functions

"""
index record
parse text
text record
link
clean
"""

index = gra_functions.create_index()
functions.post_index(index)

gra_on_pirkei_avot = gra_functions.parse()

ref = 'Gra on Pirkei Avot'
text = gra_functions.create_text(gra_on_pirkei_avot)
functions.post_text(ref, text)

list_of_links = gra_functions.create_links(gra_on_pirkei_avot)
functions.post_link(list_of_links)

testing_file = codecs.open("testing_file.txt", 'w', 'utf-8')
util.jagged_array_to_file(testing_file, gra_on_pirkei_avot, ['Perek', 'Mishna', 'Comment'])
testing_file.close()
