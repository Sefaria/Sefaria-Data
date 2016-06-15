# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys
import codecs
import re
p = os.path.dirname(os.path.abspath(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
sys.path.insert(0, p)
from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from functions import *



index = {"heSectionNames": ["\u05e4\u05e8\u05e7", "\u05e4\u05e1\u05e7\u05d4"], "title": "Megillat Taanit", "lengths": [12], "addressTypes": ["Integer", "Integer"], "heTitleVariants": ["\u05de\u05d2\u05d9\u05dc\u05ea \u05ea\u05e2\u05e0\u05d9\u05ea"], "heTitle": "\u05de\u05d2\u05d9\u05dc\u05ea \u05ea\u05e2\u05e0\u05d9\u05ea", "length": 12, "textDepth": 2, "titleVariants": ["Megillat ta'anit", "Megilat taanit", "Megillat Taanit"], "sectionNames": ["Chapter", "Paragraph"], "categories": ["Apocrypha"]}

post_index(index)