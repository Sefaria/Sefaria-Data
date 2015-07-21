# -*- coding: utf-8 -*-

import sys
import os
import pdb
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)

from sefaria.model import *
from sefaria.tracker import add
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json

def post_index(index):
	url = SEFARIA_SERVER + '/api/index/' + index["title"].replace(" ", "_")
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



root = JaggedArrayNode()
root.add_title("Tikkunei Zohar", "en", primary=True)
root.add_title(u"תקוני הזהר", "he", primary=True)

root.key = "tikkunei_zohar"
root.depth = 2
root.sectionNames = ["Daf", "Paragraph"]
root.addressTypes = ["Talmud", "Integer"]

root.validate()

index = {
	"title": "Tikkunei Zohar",
	"titleVariants": [],
	"sectionNames": ["Daf", "Paragraph"],
	"categories": ["Kabbalah"],
	"addressTypes": ["Talmud", "Integer"],
	"default_struct": "Parasha",
	"schema": root.serialize()
}


post_index(index)
Index(index).save()




