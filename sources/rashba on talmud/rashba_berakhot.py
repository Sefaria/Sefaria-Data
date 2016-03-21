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

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	

def post_index(index):
	url = SEFARIA_SERVER+'/api/index/' + index["title"].replace(" ", "_")
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
		
root=JaggedArrayNode()
root.add_title(u"Rashba on Berakhot", "en", primary=True)
root.add_title(u"""רשב״א על ברכות""", "he", primary=True)
root.key = 'rashba'
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
    "title": "Rashba on Berakhot",
    "categories": ["Commentary2", "Talmud", "Rashba"],
    "schema": root.serialize()
}

post_index(index)

