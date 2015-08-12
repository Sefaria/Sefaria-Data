# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import sys
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)

from sefaria.model import *


def post_index(index):
	url = SEFARIA_SERVER+'api/index/'+index["title"].replace(" ", "_")
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
root.key = "yalkut"
root.add_title("Yalkut Shimoni on Nach", "en", primary=True)
root.add_title(u"", "he", primary=True)


def createNodes(root_node, heb_sections, eng_sections):
	for count, word in enumerate(heb_sections):
		node = JaggedArrayNode()
		node.add_title(eng_sections[count].encode('utf-8'), "en", primary=True)
		node.add_title(word, "he", primary=True)
		node.depth = 3
		node.key = str(count)+"yalkut"
		node.sectionNames = ["Chapter", "Section", "Paragraph"]
		node.heSectionsNames = [u"פרק", u"רמז", u"פסקה"]
		node.addressTypes = ["Integer", "Integer", "Integer"]
		root_node.append(node)
		
heb_sections = [u"יהושע", u"שופטים", u"שמואל א", u"שמואל ב", u"מלכים ב", u"ישעיהו", u"ירמיהו", u"יחזקאל"


eng_sections = ["Joshua", "Judges", "I Samuel", "II Samuel", "I Kings", "II Kings", "Isaiah", "Jeremiah", "Ezekiel",
"Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi"


createNodes(root, heb_sections, eng_sections)


root.validate()


index = {
    "title": "Yalkut Shimoni on Nach",
    "categories": ["Midrash"],
    "schema": root.serialize()
}


post_index(index)

		