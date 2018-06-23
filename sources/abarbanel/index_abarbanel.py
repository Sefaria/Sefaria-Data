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
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	


root=SchemaNode()
root.add_title("Abarbanel on Torah", "en", primary=True)
root.add_title(u"אברבנאל על תורה", "he", primary=True)
root.key = 'abarbanel'

titles = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
heb_titles = [u"בראשית", u"שמות", u"ויקרא", u"במדבר", u"דברים"]
for count, title in enumerate(titles):
	node = JaggedArrayNode()
	node.add_title(heb_titles[count], 'he', primary=True)
	node.add_title(title, 'en', primary=True)
	node.depth = 3
	node.sectionNames = ["Chapter", "Verse", "Paragraph"]
	node.addressTypes = ["Integer", "Integer", "Integer"]
	node.key = title
	root.append(node)
	
root.validate()

index = { 
		"title": "Abarbanel on Torah",
		"schema": root.serialize(),
		"categories": ["Commentary2", "Tanach", "Abarbanel"]
	}
	
post_index(index)