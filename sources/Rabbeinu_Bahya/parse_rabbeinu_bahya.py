# -*- coding: utf-8 -*-
"""
Parse the text
Index Record
TextRecord
Clean Up
Link
Alternate Structure
"""

from sources.Rabbeinu_Bahya import function
from sources.Rabbeinu_Bahya import updated_structure_function
from data_utilities import util
from sources import functions

en_parsha_names = updated_structure_function.get_english_parsha_names()
he_parsha_names = updated_structure_function.get_hebrew_parsha_names()
pasuk_perek_regex = updated_structure_function.create_the_regex()
index = updated_structure_function.create_rb_indices(en_parsha_names, he_parsha_names)
functions.post_index(index)
#print updated_structure_function.create_alt_struct_dict('rabbeinu_bahya1.txt', pasuk_perek_regex)
updated_structure_function.parse_and_post('rabbeinu_bahya1.txt', pasuk_perek_regex)
