# -*- coding: utf-8 -*-
import codecs
from sefaria.model import *
import regex
from sources import functions
from parsing_utilities import util
from sources.Ralbag_on_Esther import ralbag_esther_functions

"""
index record
parse text
text record
link
clean
"""

index = ralbag_esther_functions.create_index()
functions.post_index(index)

ralbag_esther_dict = ralbag_esther_functions.parse()

for key in ralbag_esther_dict:
    ref = 'Ralbag Esther,_{}'.format(key)
    if key == 'Commentary':
        ref = 'Ralbag Esther'
    text = ralbag_esther_functions.create_text(ralbag_esther_dict[key])
    functions.post_text(ref, text)

list_of_links = ralbag_esther_functions.create_links(ralbag_esther_dict['Commentary'])
functions.post_link(list_of_links)

ralbag_esther = [ralbag_esther_dict['Introduction'], ralbag_esther_dict['Commentary'], ralbag_esther_dict['Benefits']]

util.ja_to_xml(ralbag_esther, ['FIRST', 'SECOND', 'THIRD', 'FOURTH'])