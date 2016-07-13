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


index = updated_structure_function.create_rb_indices()
functions.post_index(index)
updated_structure_function.parse_and_post('rabbeinu_bahya1.txt')
