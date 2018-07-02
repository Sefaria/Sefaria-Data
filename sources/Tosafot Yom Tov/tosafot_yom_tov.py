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
		
root = SchemaNode()
root.add_title("Tosafot Yom Tov", "en", primary=True)
root.add_title(u"תוספות יום טוב", "he", primary=True)
root.key = "tosafot_yom_tov"

sections = [("Arakhin", u"ערכין", 1), ("Avodah Zarah", u"עבודה זרה", 1), ("Avot", u"אבות", 1), 
("Berakhot", u"ברכות", 0), ("Bikkurim", u"ביכורים", 1), ("Challah", u"חלה", 1), ("Demai", u"דמאי", 1),
("Eduyot", u"עדיות", 1), ("Eruvin", u"עירובין", 1), ("Gittin", u"גיטין", 1), ("Horayot", u"הוריות", 1),
("Kinnim", u"קינים", 1), ("Kiddushin", u"קידושין", 1), ("Kilayim", u"כלאים", 1), ("Maaser Sheni", u"מעשר שני", 1),
("Maasrot", u"מעשרות", 1), ("Meilah", u"מעילה", 1), ("Nazir", u"נזיר", 1), ("Oholot", u"אהלות", 1),
("Parah", u"פרה", 0), ("Peah", u"פאה", 1), ("Pesachim", u"פסחים", 1), ("Shevuot", u"שבועות", 1),
("Sheviit", u"שביעית", 1), ("Sotah", u"סוטה", 1), ("Tamid", u"תמיד", 1), ("Temurah", u"תמורה", 1),
("Yevamot", u"יבמות", 1)]

for sec in sections:
	if sec[2] == 1:
		intro_node = JaggedArrayNode()
		intro_node.add_title(sec[0]+", Introduction", "en", primary=True)
		intro_node.add_title(sec[1]+u", הקדמה", "he", primary=True)
		intro_node.key = 'intro'+sec[0]
		intro_node.sectionNames = ["Paragraph"]
		intro_node.depth = 1
		intro_node.addressTypes = ["Integer"]
		root.append(intro_node)
	main_node = JaggedArrayNode()
	main_node.add_title(sec[0], "en", primary=True)
	main_node.add_title(sec[1], "he", primary=True)
	main_node.key = sec[0]
	main_node.sectionNames = ["Perek", "Mishnah", "Comment"]
	main_node.depth = 3
	main_node.addressTypes = ["Integer", "Integer", "Integer"]
	root.append(main_node)
	
root.validate()

index = {
    "title": "Tosafot Yom Tov",
    "categories": ["Mishnah", "Commentary"],
    "schema": root.serialize()
}


post_index(index)
	