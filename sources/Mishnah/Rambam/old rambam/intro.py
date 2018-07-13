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
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)

from sefaria.model import *


def post_index(index):
	url = 'http://www.sefaria.org/api/index/' + index["title"].replace(" ", "_")
	indexJSON = json.dumps(index)
	print indexJSON
	values = {
		'json': indexJSON, 
		'apikey': 'F4J2j3RF6fHWHLtmAtOTeZHE3MOIcsgvcgtYSwMzHtM'
	}
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	try:
		response = urllib2.urlopen(req)
		print response.read()
	except HTTPError, e:
		print 'Error code: ', e.code

root = JaggedArrayNode()
root.key = 'rambam_intro'
root.add_title("Introduction to Seder Kodashim", "en", primary=True)
root.add_title(u"הקדמה לסדר קודשים", "he", primary=True)
root.sectionNames = ["Paragraph"]
root.addressTypes = ["Integer"]
root.depth = 1


root.validate()


index = {
    "title": "Introduction to Seder Kodashim",
    "categories": ["Commentary2", "Mishnah", "Seder Kodashim"],
    "schema": root.serialize()
}


post_index(index)
