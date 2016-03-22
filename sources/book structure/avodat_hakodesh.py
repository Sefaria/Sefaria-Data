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
	url = SEFARIA_SERVER+'/api/v2/raw/index/' + index["title"].replace(" ", "_")
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
	
root = SchemaNode()
root.key = 'avodat'
root.add_title("Avodat HaKodesh", "en", primary=True)
root.add_title(u"עבודת הקדש", "he", primary=True)

part1 = SchemaNode()
part1.key = 'part1'
part1.add_title(u"חלק א': בית נתיבות", "he", primary=True)
part1.add_title("Part One, Beit Netivot", "en", primary=True)

intro = JaggedArrayNode()
intro.key = 'intro'
intro.add_title("Introduction", "en", primary=True)
intro.add_title(u"הקדמה", "he", primary=True)
intro.depth = 1
intro.sectionNames = ["Paragraph"]
intro.addressTypes = ["Integer"]
part1.append(intro)


part2 = SchemaNode()
part2.key = 'part2'
part2.add_title("Part Two, Beit Moed", "en", primary=True)
part2.add_title(u"חלק ב': בית מועד", "he", primary=True)

heb_sections = [u"השער הראשון", u"השער השני", u"השער השלישי", u"השער הרביעי", u"השער החמישי"]
eng_sections = ["The First Gate", "The Second Gate", "The Third Gate", "The Fourth Gate", "The Fifth Gate"]

for count, word in enumerate(eng_sections):
	gate1 = JaggedArrayNode()
	gate1.key = 'gate'+str(count)
	gate1.add_title(heb_sections[count], "he", primary=True)
	gate1.add_title(word, "en", primary=True)
	gate1.sectionNames = ["Paragraph"]
	gate1.addressTypes = ["Integer"]
	gate1.depth = 1
	part1.append(gate1)
	part2.append(gate1)


root.append(part1)
root.append(part2)
		
		

root.validate()


index = {
    "title": "Avodat HaKodesh",
    "categories": ["Halakhah"],
    "schema": root.serialize()
}


post_index(index)

