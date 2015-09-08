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

root=SchemaNode()
root.add_title("Tanna debei Eliyahu Zuta", "en", primary=True)
root.add_title(u"תנא דבי אליהו זוטא", "he", primary=True)
root.key = "tanna"

seder = SchemaNode()
seder.add_title("Seder Eliyahu Zuta", "en", primary=True)
seder.add_title(u"סדר אליהו זוטא", "he", primary=True)
seder.key = "seder"

contents = JaggedArrayNode()
contents.lengths = [15]
contents.depth = 2
contents.default = True
contents.key = "default"
contents.sectionNames = ["Chapter", "Paragraph"]
contents.addressTypes = ["Integer", "Integer"]
contents.validate()

seder.append(contents)
seder.validate()


intro = JaggedArrayNode()
intro.add_title(u"הקדמה", "he", primary=True)
intro.add_title("Hakdamah", "en", primary=True)
intro.key = "intro"
intro.sectionNames = ["Paragraph"]
intro.addressTypes = ["Integer"]
intro.depth = 1

mavo = JaggedArrayNode()
mavo.key = "mavo"
mavo.add_title("Mavo", "en", primary=True)
mavo.add_title(u"מבוא", "he", primary=True)
mavo.depth = 1
mavo.sectionNames = ["Paragraph"]
mavo.addressTypes = ["Integer"]
mavo.validate()

pirkei1 = JaggedArrayNode()
pirkei1.key = "p1"
pirkei1.add_title("Pirkei Derech Eretz", "en", primary=True)
pirkei1.add_title(u"פרקי דרך ארץ", "he", primary=True)
pirkei1.depth = 1
pirkei1.sectionNames = ["Paragraph"]
pirkei1.addressTypes = ["Integer"]
pirkei1.validate()

pirkei2 = JaggedArrayNode()
pirkei2.key = "p2"
pirkei2.depth = 1
pirkei2.sectionNames = ["Paragraph"]
pirkei2.addressTypes = ["Integer"]
pirkei2.add_title("Pirkei DeRabbi Eliezer", "en", primary=True)
pirkei2.add_title(u"פרקי דר' אליעזר", "he", primary=True)
pirkei2.validate()

pirkei3 = JaggedArrayNode()
pirkei3.key = "p3"
pirkei3.depth = 1
pirkei3.sectionNames = ["Paragraph"]
pirkei3.addressTypes = ["Integer"]
pirkei3.add_title("Pirkei HaYeridot", "en", primary=True)
pirkei3.add_title(u"הירידות", "he", primary=True)
pirkei3.validate()

addition = SchemaNode()
addition.add_title(u"נספחים לסדר אליהו זוטא", "he", primary=True)
addition.add_title("Additions to Seder Eliyahu Zuta", "en", primary=True)
addition.key = "addition"
addition.validate()

addition.append(intro)
addition.append(mavo)
addition.append(pirkei1)
addition.append(pirkei2)
addition.append(pirkei3)

root.append(seder)
root.append(addition)


root.validate()


index = {
    "title": "Tanna debei Eliyahu Zuta",
    "categories": ["Midrash"],
    "schema": root.serialize()
}


post_index(index)

