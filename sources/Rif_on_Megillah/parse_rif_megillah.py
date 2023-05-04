# -*- coding: utf-8 -*-
import codecs
from sefaria.model import *
import regex
from sources import functions
from parsing_utilities import util
from sources.Rif_on_Megillah import rif_megillah_functions

"""
index record
parse text
text record
link
clean
"""

index = rif_megillah_functions.create_index()
functions.post_index(index)

rif_megillah = rif_megillah_functions.parse()

ref = 'Rif_Megillah'
text = rif_megillah_functions.create_text(rif_megillah)
functions.post_text(ref, text)

testing_file = codecs.open("testing_file.txt", 'w', 'utf-8')
util.jagged_array_to_file(testing_file, rif_megillah, ['Daf', 'Line'])
testing_file.close()
