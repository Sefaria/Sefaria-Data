# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
from sources.Lechem_Shamayim_on_Avot import ls_functions
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

ls_index = ls_functions.create_index()
functions.post_index(ls_index)
lechem_shamayim_ja = ls_functions.parse_and_post('ls_on_avot.txt')
ls_functions.create_links(lechem_shamayim_ja)