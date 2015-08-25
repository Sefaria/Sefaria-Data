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
	url = SEFARIA_SERVER+'api/v2/raw/index/'+index["title"].replace(" ", "_")
	indexJSON = json.dumps(index)
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

root = JaggedArrayNode()
root.key = "yalkut_on_nach"
root.add_title("Yalkut Shimoni on Nach", "en", primary=True)
root.add_title(u"""ילקות שמעוני על נ״ח""", "he", primary=True)
root.depth = 2
root.sectionNames = ["Remez", "Paragraph"]
root.heSectionNames = [u"רמז", u"פסקה"]
root.addressTypes = ["Integer", "Integer"]

root.validate()


index = {
    "title": "Yalkut Shimoni on Nach",
    "categories": ["Midrash"],
    "schema": root.serialize()
}


post_index(index)
