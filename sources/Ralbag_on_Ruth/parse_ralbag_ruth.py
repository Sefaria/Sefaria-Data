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

ralbag_ruth_dict = ralbag_ruth_functions.parse()

for key in ralbag_ruth_dict:
    ref = 'Ralbag Ruth'
    if key == 'Benefits':
        ref += ',_Benefits'
    text = ralbag_ruth_functions.create_text(ralbag_ruth_dict[key])
    functions.post_text(ref, text)

list_of_links = ralbag_ruth_functions.create_links(ralbag_ruth_dict['Commentary'])
functions.post_link(list_of_links)

ralbag_ruth = [ralbag_ruth_dict['Commentary'], ralbag_ruth_dict['Benefits']]

util.ja_to_xml(ralbag_ruth, ['FIRST', 'SECOND', 'THIRD', 'FOURTH'])
