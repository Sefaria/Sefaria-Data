# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from parsing_utilities import util
from sources.Targum_Isaiah_English import ti_functions

targum_isaiah = ti_functions.parse_targum_isaiah_english()

# ref = 'Targum Isaiah'
# text = ti_functions.create_text(targum_isaiah)
# functions.post_text(ref, text)

testing_file = codecs.open("testing_file.txt", 'w', 'utf-8')
util.jagged_array_to_file(testing_file, targum_isaiah, ['Chapter', 'Verse'])
testing_file.close()
