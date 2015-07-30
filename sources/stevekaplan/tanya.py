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

root = SchemaNode()
root.add_title("Tanya", "en", primary=True)
root.add_title(u"תניא", "he", primary=True)
root.add_title("Likutei Amarim", "en", primary=False)
root.add_title(u"לקוטי אמרים", "he", primary=False)
root.key = "tanya"

intro = JaggedArrayNode()
intro.add_title("Introduction", "en", primary=True)
intro.add_title(u"הקדמה", "he", primary=True)
intro.key = "intro"
intro.depth = 1
intro.sectionNames = ["Paragraph"]
intro.addressTypes = ["Integer"]

part1 = JaggedArrayNode()
part1.add_title("Part One, The Book of the Average Men", "en", primary=True)
part1.add_title(u"חלק ראשון, ספר של בינונים", "he", primary=True)
part1.key="part1"
part1.depth = 2
part1.sectionNames = ["Chapter", "Paragraph"]
part1.lengths = [53]
part1.addressTypes = ["Integer", "Integer"]

part2 = SchemaNode()
part2.add_title("Part Two, The Gateway of Unity and Belief", "en", primary=True)
part2.add_title(u"חלק שני, שער היחוד והאמונה", "he", primary=True)
part2.key = "part2"

part2a = JaggedArrayNode()
part2a.add_title(u"חינוך קטן", "he", primary=True)
part2a.add_title("The Education of the Child", "en", primary=True)
part2a.depth = 1
part2a.key = "part2a"
part2a.sectionNames = ["Paragraph"]
part2a.addressTypes = ["Integer"]

part2b = JaggedArrayNode()
part2b.default = True
part2b.key="default"
part2b.depth = 2
part2b.lengths = [12]
part2b.sectionNames = ["Chapter", "Paragraph"]
part2b.addressTypes = ["Integer", "Integer"]

part2.append(part2a)
part2.append(part2b)

letter1 = JaggedArrayNode()
letter1.add_title(u"אגרת התשובה", "he", primary=True)
letter1.add_title("Letter of Repentance", "en", primary=True)
letter1.depth = 2
letter1.lengths = [12]
letter1.key = "letter1"
letter1.sectionNames = ["Chapter", "Paragraph"]
letter1.addressTypes = ["Integer", "Integer"]

letter2 = JaggedArrayNode()
letter2.add_title(u"אגרת הקדש", "he", primary=True)
letter2.add_title("Letter of Holiness", "en", primary=True)
letter2.depth = 2
letter2.lengths = [32]
letter2.key = "letter2"
letter2.sectionNames = ["Chapter", "Paragraph"]
letter2.addressTypes = ["Integer", "Integer"]

last = JaggedArrayNode()
last.add_title("Last Thesis", "en", primary=True)
last.add_title(u"קונטרס אחרון", "he", primary=True)
last.depth = 2
last.lengths = [9]
last.key = "last"
last.sectionNames = ["Chapter", "Paragraph"]
last.addressTypes = ["Integer", "Integer"]

root.append(intro)
root.append(part1)
root.append(part2)
root.append(letter1)
root.append(letter2)
root.append(last)

root.validate()


index = {
    "title": "Tanya",
    "titleVariants": ["Likutei Amarim", "Sefer haTanya"],
    "categories": ["Chasidut"],
    "schema": root.serialize()
}


post_index(index)
