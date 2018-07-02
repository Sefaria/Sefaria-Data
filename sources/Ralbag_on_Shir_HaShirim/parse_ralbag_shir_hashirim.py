# -*- coding: utf-8 -*-
import codecs
from sefaria.model import *
import regex
from sources import functions
from data_utilities import util
from sources.Ralbag_on_Shir_HaShirim import ralbag_shir_hashirim_functions

"""
index record
parse text
text record
link
clean
"""

index = ralbag_shir_hashirim_functions.create_index()
functions.post_index(index)

ralbag_shir_hashirim_dict = ralbag_shir_hashirim_functions.parse()

for key in ralbag_shir_hashirim_dict:
    ref = 'Ralbag Song of Songs'
    if key == 'Introduction':
        ref += ',_Introduction'
    text = ralbag_shir_hashirim_functions.create_text(ralbag_shir_hashirim_dict[key])
    functions.post_text(ref, text)

list_of_links = ralbag_shir_hashirim_functions.create_links(ralbag_shir_hashirim_dict['Commentary'])
functions.post_link(list_of_links)

ralbag_ruth = [ralbag_shir_hashirim_dict['Introduction'], ralbag_shir_hashirim_dict['Commentary']]

util.ja_to_xml(ralbag_ruth, ['FIRST', 'SECOND', 'THIRD', 'FOURTH'])
