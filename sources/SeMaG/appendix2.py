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

root = SchemaNode()
root.add_title("Sefer Mitzvot Gadol", "en", primary=True)
root.add_title("SeMaG", "en")
root.add_title(u"ספר מצוות גדול", "he", primary=True)
root.add_title(u'סמ"ג', 'he')
root.key = "smg"


vol1 = JaggedArrayNode()
vol1.key = 'vol1'
vol1.add_title("Volume One", "en", primary=True)
vol1.add_title(u"חלק הלאוין", "he", primary=True)
vol1.sectionNames = ["Negative Mitzvah", "Paragraph"]
vol1.addressTypes = ["Integer", "Integer"]
vol1.depth = 2

vol2 = SchemaNode()
vol2.key = 'vol2'
vol2.add_title("Volume Two", "en", primary=True)
vol2.add_title(u"חלק העשין", "he", primary=True)

default_node = JaggedArrayNode()
default_node.depth = 2
default_node.sectionNames = ["Positive Mitzvah", "Paragraph"]
default_node.addressTypes = ["Integer", "Integer"]
default_node.default = True
default_node.key = "default"

vol2.append(default_node)

heb_nodes = [u"הלכות עירובין", u"הלכות אבילות", u"הלכות תשעה באב", u"הלכות מגילה", u"הלכות חנוכה"]
eng_nodes = ["Laws of Eruvin", "Laws of Mourning", "Laws of Tisha B'Av", "Laws of Megillah", "Laws of Chanukah"]
for count, heb_node in enumerate(heb_nodes):
	node = JaggedArrayNode()
	node.depth = 1
	node.sectionNames = ["Paragraph"]
	node.addressTypes = ["Integer"]
	node.key = eng_nodes[count]
	node.add_title(heb_node, "he", primary=True)
	node.add_title(eng_nodes[count], "en", primary=True)
	vol2.append(node)



def addMitzvah(mitzvah, text):
	if not isGematria(mitzvah):
		print 'not gematria!'
		pdb.set_trace()
	current_mitzvah = getGematria(mitzvah)
	if current_mitzvah in text:
		print "double mitzvah"
		pdb.set_trace()
	return current_mitzvah
	
smag = open("appendix.txt",'r')
tag = re.compile('@\d+')
text = {}
prev_line=""
msg=""

root.append(vol1)
root.append(vol2)
root.validate()
index = {
	"title": "Sefer Mitzvot Gadol",
	"categories": ["Halakhah"],
	"schema": root.serialize()
	}
post_index(index)