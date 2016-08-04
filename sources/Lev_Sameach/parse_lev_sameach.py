# -*- coding: utf-8 -*-
import codecs
from sefaria.model import *
import regex
from sources import functions
from data_utilities import util
from sources.Lev_Sameach import ls_functions

"""
index record
parse text
text record
link
clean
"""

index = ls_functions.create_index()
functions.post_index(index)

lev_sameach = ls_functions.parse()

a = ['Shorashim', 'Positive_Commandments', 'Negative_Commandments']
for index, each_depth_two in enumerate(lev_sameach):
    ref = 'Lev Sameach,_{}'.format(a[index])
    text = ls_functions.create_text(each_depth_two)
    functions.post_text(ref, text)


list_of_links = ls_functions.create_links(lev_sameach[0])
functions.post_link(list_of_links)

testing_file = codecs.open("testing_file.txt", 'w', 'utf-8')
util.jagged_array_to_file(testing_file, lev_sameach, ['DEPTH ONE', 'DEPTH TWO', 'DEPTH THREE'])
testing_file.close()
