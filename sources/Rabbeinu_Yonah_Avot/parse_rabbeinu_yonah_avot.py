# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
from sources.Rabbeinu_Yonah_Avot import rb_yonah_functions
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode
from fuzzywuzzy import fuzz
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys

"""
Parse
Link
Clean
index record
text record
"""
# pirkei_avot_ja = TextChunk(Ref('Pirkei Avot'), 'he').text

rb_index = rb_yonah_functions.create_index()
functions.post_index(rb_index)
rb_yonah_ja = rb_yonah_functions.parse_and_post('rabbeinu_yonah_on_avot.txt')
rb_yonah_functions.create_links(rb_yonah_ja)