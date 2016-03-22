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
	url = SEFARIA_SERVER+'/api/v2/raw/index/' + index["title"].replace(" ", "_")
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
root.add_title("Sha'ar HaMayim HaAroch", "en", primary=True)
root.add_title(u"שער המים הארוך", "he", primary=True)
root.key = "shaar"

heb_sections = [u"פתיחה", u"השער הראשון", u"השער השני", u"השער השלישי", u"השער הרביעי", u"השער החמישי", u"השער השישי", 
u"השער השביעי", u"השער השמיני", u"השער התשיעי", u"השער העשירי", u"השער האחד עשרה"]
eng_sections = ["Preface", "The First Gate", "The Second Gate", "The Third Gate", "The Fourth Gate", "The Fifth Gate",
"The Sixth Gate", "The Seventh Gate", "The Eighth Gate", "The Ninth Gate", "The Tenth Gate", "The Eleventh Gate"]

for count, title in enumerate(eng_sections):
	node = JaggedArrayNode()
	node.key = str(count)+title
	node.add_title(title, "en", primary=True)
	node.add_title(heb_sections[count], "he", primary=True)
	node.sectionNames = ["Paragraph"]
	node.addressTypes = ["Integer"]
	node.depth = 1
	root.append(node)
	
root.validate()


index = {
    "title": "Sha'ar HaMayim HaAroch",
    "categories": ["Halakhah"],
    "schema": root.serialize()
}


post_index(index)


