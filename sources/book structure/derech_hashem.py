# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import sys
p = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)

from sefaria.model import *


def post_index(index):
	url = SEFARIA_SERVER+'api/v2/raw/index/'+index["title"].replace(" ", "_")
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
root.add_title("Redeeming Relevance", "en", primary=True)
root.add_title(u"", "he", primary=True)
root.key = 'root'

intro=JaggedArrayNode()
intro.depth = 1
intro.sectionNames = ["Paragraph"]
intro.addressTypes = ["Integer"]
intro.add_title("Approbation of Rabbi Dr. Aharon Lichtenstein", "en", primary=True)
intro.add_title(u"הסכמה", "he", primary=True)
intro.key='intro'
intro.validate()
root.append(intro)

heb_titles = [u"בראשית א", u"שמות ג", u"במדבר ו"]
titles = ["Genesis Chapter 1", "Exodus Chapter 3", "Bamidbar Chapter 6"]
for count, title in enumerate(titles):
	node = JaggedArrayNode()
	node.depth = 1
	node.sectionNames = ["Paragraph"]
	node.addressTypes = ["Integer"]
	node.add_title(title, "en", primary=True)
	node.add_title(heb_titles[count], "he", primary=True)
	root.append(node)


index = {
    "title": u"Redeeming Relevance",
    "categories": ["Modern Works"],
    "schema": root.serialize()
}


post_index(index)
