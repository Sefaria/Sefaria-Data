# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from parsing_utilities import util
from sources.Rabbeinu_Yonah_Avot import rb_yonah_functions


"""
Parse
Link
Clean
index record
text record
"""

rb_index = rb_yonah_functions.create_index()
functions.post_index(rb_index)
rb_yonah_ja = rb_yonah_functions.parse_and_post('rabbeinu_yonah_on_avot.txt')
rb_yonah_functions.create_links(rb_yonah_ja)