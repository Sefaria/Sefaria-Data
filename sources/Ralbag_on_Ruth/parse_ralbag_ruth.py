# -*- coding: utf-8 -*-
import codecs
from sefaria.model import *
import regex
from sources import functions
from data_utilities import util
from sources.Ralbag_on_Ruth import ralbag_ruth_functions

"""
index record
parse text
text record
link
clean
"""

index = ralbag_ruth_functions.create_index()
functions.post_index(index)

ralbag_ruth = ralbag_ruth_functions.parse()

for index, each_text in enumerate(ralbag_ruth):
    ref = 'Ralbag on Ruth'
    if index == 1:
        ref += ',_Benefits'
    text = ralbag_ruth_functions.create_text(each_text)
    functions.post_text(ref, text)

list_of_links = ralbag_ruth_functions.create_links(ralbag_ruth[0])
functions.post_link(list_of_links)


util.ja_to_xml(ralbag_ruth, ['FIRST', 'SECOND', 'THIRD', 'FOURTH'])
