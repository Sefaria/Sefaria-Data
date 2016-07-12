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
from data_utilities import util
from sources import functions


index = function.create_indices()
functions.post_index(index)
# function.parse_and_post('rabbeinu_bahya1.txt')
