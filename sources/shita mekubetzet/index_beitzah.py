# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import sys
from bs4 import BeautifulSoup
import re
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	


root=JaggedArrayNode()
root.add_title(u"Shita Mekubetzet on Beitzah", "en", primary=True)
root.add_title(u"שיטה מקובצת על ביצה", "he", primary=True)
root.key = 'shita'
root.sectionNames = ["Daf", "Comment"]
root.depth = 2
root.addressTypes = ["Talmud","Integer"]



root.validate()
'''
"categories" : [
  "Commentary2",
  "Talmud",
  "Bavli",
  Index().load({"title":masechet}).categories[2],
  "%s" % masechet
  '''
index = {
    "title": "Shita Mekubetzet on Beitzah",
    "categories": ["Commentary2", "Talmud", "Shita Mekubetzet"],
    "schema": root.serialize()
}

post_index(index)

