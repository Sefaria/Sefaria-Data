# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sources.Targum_Jerusalem_in_English import tj_functions
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode
from fuzzywuzzy import fuzz
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys


all_five_book = tj_functions.parse_targum_jerusalem_english()

testing_file = codecs.open("testing_file.txt", 'w', 'utf-8')
util.jagged_array_to_file(testing_file, all_five_book,['Book', 'Chapter', 'Verse'])
testing_file.close()