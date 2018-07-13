# -*- coding: utf-8 -*-
import codecs
from sefaria.model import *
import regex
from sources import functions
from data_utilities import util
from sources.Rif_on_Nedarim import rif_nedarim_functions

"""
index record
parse text
text record
link
clean
"""

index = rif_nedarim_functions.create_index()
functions.post_index(index)

rif_nedarim = rif_nedarim_functions.parse()

ref = 'Rif_Nedarim'
text = rif_nedarim_functions.create_text(rif_nedarim)
functions.post_text(ref, text)

testing_file = codecs.open("testing_file.txt", 'w', 'utf-8')
util.jagged_array_to_file(testing_file, rif_nedarim, ['Daf', 'Line'])
testing_file.close()

util.ja_to_xml(rif_nedarim, ['Daf', 'Line'])