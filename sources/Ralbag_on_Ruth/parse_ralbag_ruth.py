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

# index = ralbag_ruth_functions.create_index()
# functions.post_index(index)

ralbag_ruth = ralbag_ruth_functions.parse()

# ref = 'Ralbag on Ruth'
# text = ralbag_ruth_functions.create_text(ralbag_ruth)
# functions.post_text(ref, text)


util.ja_to_xml(ralbag_ruth, ['FIRST', 'SECOND', 'THIRD', 'FOURTH'])
