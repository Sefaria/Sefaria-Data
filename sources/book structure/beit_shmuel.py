# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import re
import sys
p = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)

from sefaria.model import *



def post_index(index):
	url = SEFARIA_SERVER+'api/index/' + index["title"].replace(" ", "_")
	indexJSON = json.dumps(index)
	print indexJSON
	values = {
		'json': indexJSON, 
		'apikey': API_KEY
			}
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	try:
		response = urllib2.urlopen(req)
		print response.read()
	except HTTPError, e:
		print 'Error code: ', e.code
		
		
root = SchemaNode()
root.add_title("Beit Shmuel", "en", primary=True)
root.add_title(u"בית שמואל", "he", primary=True)
root.key="beitshmuel"

contents = JaggedArrayNode()
contents.key = "default"
contents.default = True
contents.depth = 2
contents.sectionNames = ["Siman", "Seif Katan"]
contents.heSectionNames = [u"סימן", u"סעיף קטן"]
contents.addressTypes = ["Integer", "Integer"]



intro = JaggedArrayNode()
intro.key = "intro"
intro.add_title(u"בית שמואל שמות אנשים ונשים הקדמה ", "he", primary=True)
intro.add_title("Introduction to Section on Names", "en", primary=True)
intro.depth = 1
intro.sectionNames = ["Paragraph"]
intro.addressTypes = ["Integer"]

men = JaggedArrayNode()
men.key = "men"
men.depth = 1
men.add_title("Beit Shmuel on Names for Men", "en", primary=True)
men.add_title(u"בית שמואל שמות אנשים ונשים שמות אנשים", "he", primary=True)
men.sectionNames = ["Paragraph"]
men.addressTypes = ["Integer"]

women = JaggedArrayNode()
women.key = "women"
women.depth = 1
women.add_title("Beit Shmuel on Names for Women", "en", primary=True)
women.add_title(u"בית שמואל שמות אנשים ונשים שמות נשים", "he", primary=True)
women.sectionNames = ["Paragraph"]
women.addressTypes = ["Integer"]

rivers = JaggedArrayNode()
rivers.key = "rivers"
rivers.depth = 1
rivers.sectionNames = ["Paragraph"]
rivers.addressTypes = ["Integer"]
rivers.add_title("Beit Shmuel on Names of Rivers", "en", primary=True)
rivers.add_title(u"בית שמואל שמות אנשים ונשים שמות עיירות ונהרות", "he", primary=True)


final = JaggedArrayNode()
final.key = "final"
final.depth = 1
final.sectionNames = ["Paragraph"]
final.addressTypes = ["Integer"]
final.add_title("Beit Shmuel on Names", "en", primary=True)
final.add_title(u"בית שמואל שמות אנשים ונשים כללים", "he", primary=True)

root.append(contents)
root.append(intro)
root.append(men)
root.append(women)
root.append(rivers)
root.append(final)

root.validate()

index = {
    "title": "Beit Shmuel",
    "categories": ["Halakhah"],
    "schema": root.serialize()
}

post_index(index)
