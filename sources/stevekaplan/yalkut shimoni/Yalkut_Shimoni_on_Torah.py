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
	url = SEFARIA_SERVER+'api/index/'+index["title"].replace(" ", "_")
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
root.key = "yalkut"
root.add_title("Yalkut Shimoni on Torah", "en", primary=True)
root.add_title(u"ילקוט שמעוני על התורה", "he", primary=True)


def createNodes(root_node, heb_sections, eng_sections):
	for count, word in enumerate(heb_sections):
		node = JaggedArrayNode()
		node.add_title(eng_sections[count].encode('utf-8'), "en", primary=True)
		node.add_title(word, "he", primary=True)
		node.depth = 2
		node.key = str(count)+"yalkut"
		node.sectionNames = ["Section", "Paragraph"]
		node.heSectionsNames = [u"רמז", u"פסקה"]
		node.addressTypes = ["Integer", "Integer"]
		root_node.append(node)
		
heb_sections = [u"בראשית",u"נח", u"לך לך", u"וירא", u"חיי שרה", u"תולדות", u"ויצא", u"וישלח", u"וישב", u"מקץ",
u"ויגש", u"ויחי", u"שמות", u"וארא", u"בא", u"בשלח", u"יתרו", u"משפטים", u"תרומה", u"תצוה", u"כי תשא",
u"ויקהל", u"פקודי", u"ויקרא", u"צו", u"שמיני", u"תזריע", u"מצרע", u"אחרי מות", u"קדשים", u"אמר", u"בהר",
u"בחקתי", u"במדבר", u"נשא", u"בהעלתך", u"שלח לך", u"קרח", u"חקת", u"בלק", u"פינחס", u"מטות", 
u"מסעי", u"דברים", u"ואתחנן", u"עקב", u"ראה", u"שפטים", u"כי תצא", u"כי תבוא", u"נצבים",
u"וילך", u"האזינו", u"וזאת הברכה"]

eng_sections = ["Bereishit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach",
"Vayeshev", "Miketz", "Vayigash", "Vayechi", "Shemot", "Vaera", "Bo", "Beshalach", "Yitro",
"Mishpatim", "Terumah", "Tetzaveh", "Ki Tisa", "Vayakhel", "Pekudei", "Vayikra", "Tzav", "Shmini",
"Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar", "Bechukotai", "Bamidbar", "Nasso",
"Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei",
"Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo", "Nitzavim", "Vayeilech", "Ha'Azinu",
"V'Zot HaBerachah"]

createNodes(root, heb_sections, eng_sections)


root.validate()


index = {
    "title": "Yalkut Shimoni on Torah",
    "categories": ["Midrash"],
    "schema": root.serialize()
}


post_index(index)
