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
root.key = 'torathabayit'
root.add_title("Torat HaBayit HaAroch", "en", primary=True)
root.add_title(u"תורת הבית הארוך", "he", primary=True)

heb_houses = [u"הבית הראשון", u"הבית השני", u"הבית השלישי", u"הבית הרביעי", u"הבית החמישי", u"הבית השישי", u"הבית השביעי: בית הנשים"]
eng_houses = ["The First House", "The Second House", "The Third House", "The Fourth House", "The Fifth House",
"The Sixth House", "The Seventh House, The Women's House"]
heb_gates = [u"השער הראשון", u"השער השני", u"השער השלישי", u"השער הרביעי", u"השער החמישי", u"השער השישי", 
u"השער השביעי"]
eng_gates = ["The First Gate", "The Second Gate", "The Third Gate", "The Fourth Gate",
"The Fifth Gate", "The Sixth Gate", "The Seventh Gate"]

intro = JaggedArrayNode()
intro.key = 'intro'
intro.add_title("Introduction", "en", primary=True)
intro.add_title(u"הקדמה", "he", primary=True)
intro.depth = 1
intro.sectionNames = ["Paragraph"]
intro.addressTypes = ["Integer"]

root.append(intro)

how_many_gates = [5, 5, 7, 4, 6, 5, 7]
for count, house in enumerate(heb_houses):
	node = SchemaNode()
	node.add_title(house, "he", primary=True)
	node.add_title(eng_houses[count], "en", primary=True)
	node.key = 'house'+str(count)
	for gate_count, gate in enumerate(heb_gates):
		if gate_count == how_many_gates[count]:
			break
		if gate_count == 0 and count == 6:
			intro_node = JaggedArrayNode()
			intro_node.depth = 1
			intro_node.sectionNames = ["Paragraph"]
			intro_node.addressTypes = ["Integer"]
			intro_node.key = "intro_gate"
			intro_node.add_title("Introduction", "en", primary=True)
			intro_node.add_title(u"הקדמה", "he", primary=True)
			node.append(intro_node)
		gate_node = JaggedArrayNode()
		gate_node.depth = 1
		gate_node.add_title(gate, "he", primary=True)
		gate_node.add_title(eng_gates[gate_count], "en", primary=True)
		gate_node.key = 'gate'+str(gate_count)
		gate_node.sectionNames = ["Paragraph"]
		gate_node.addressTypes = ["Integer"]
		node.append(gate_node)
	root.append(node)	

root.validate()


index = {
    "title": "Torat HaBayit HaAroch",
    "categories": ["Halakhah"],
    "schema": root.serialize()
}


post_index(index)
