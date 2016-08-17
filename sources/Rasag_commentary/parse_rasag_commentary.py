# -*- coding: utf-8 -*-
import codecs
from sefaria.model import *
import regex
from sources import functions
from data_utilities import util
from sources.Rasag_commentary import rasag_commentary_index_record

"""
index record
parse text
text record
link
clean
"""

index = rasag_commentary_index_record.create_index()
functions.post_index(index)

rasag_commentary = rasag_commentary_index_record.parse()

for key in rasag_commentary:
    ref = 'Rasag Commentary,_{}'.format(key)
    if key == 'Commentary':
        ref = 'Ralbag Esther'
    text = rasag_commentary_index_record.create_text(rasag_commentary[key])
    functions.post_text(ref, text)

list_of_links = rasag_commentary_index_record.create_links(rasag_commentary['Commentary'])
functions.post_link(list_of_links)

rasag_commetary_ja = [rasag_commentary['Introduction'], rasag_commentary['Commentary'], rasag_commentary['Benefits']]

util.ja_to_xml(rasag_commetary_ja, ['FIRST', 'SECOND', 'THIRD', 'FOURTH'])