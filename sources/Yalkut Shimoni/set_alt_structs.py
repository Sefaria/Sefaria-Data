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

def post_index(index):
	url = SEFARIA_SERVER + '/api/v2/raw/index/Yalkut_Shimoni_on_Torah'
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
	
def convertIntoRef(line):
	arr = line.split(",")
	perek = arr[0]
	remez = arr[1]
	para = arr[2]
	return (perek, Ref("Yalkut Shimoni on Torah."+remez+"."+para))

perakim = {}
perakim = { "nodes" : [] }
parshiot = { "nodes": [] }

title_eng = ["Bereishit", "Shemot", "Vayikra", "Bamidbar", "Devarim"]
title_heb = [u"בראשית", u"שמות", u"ויקרא", u"במדבר", u"דברים"]
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

def getHebrewParsha(parsha):
	for count, eng in enumerate(eng_sections):
		if eng==parsha:
			return heb_sections[count]

for count, title in enumerate(title_eng):
	f=open("parsha_"+title+".txt", 'r')
	while True:
		line = f.readline()
		if line == '':
			break
		parsha_name, start_ref = convertIntoRef(line)
		#if parsha_name == "Shoftim" or parsha_name == "Nitzavim" or parsha_name == "Vayeilech":
		#	continue
		line = f.readline()
		parsha_name, end_ref = convertIntoRef(line)
		wholeRef = start_ref.to(end_ref).normal()
		parsha = ArrayMapNode()
		parsha.add_title(parsha_name, "en", primary=True)
		parsha.add_title(getHebrewParsha(parsha_name), "he", primary=True)
		parsha.key = parsha_name
		parsha.depth = 0
		parsha.addressTypes = []
		parsha.sectionNames = []
		parsha.wholeRef = wholeRef
		parsha.refs = []
		parshiot["nodes"].append(parsha.serialize())

for count, title in enumerate(title_eng):
	f=open("perek_"+title+".txt", 'r')
	line = "nothing"
	first_one = ""
	last_one = ""
	refs_dict = {}
	current = 0
	while line != '':
		prev_line = line
		line = f.readline()
		if line == '':
			break
		start_perek, start_ref = convertIntoRef(line)
		if prev_line == "nothing":
			first_one = (start_perek, start_ref)
		line = f.readline()
		end_perek, end_ref = convertIntoRef(line)
		last_one = (end_perek, end_ref)
		#the line below is simply to not generate the error
		if title=='Devarim' and (start_perek == '17' or start_perek == '29' or start_perek == '30' or start_perek == '31'):
			continue
		if start_perek == end_perek:
			refs_dict[start_perek] = start_ref.to(end_ref).normal()
	refs = []
	for i in range(int(last_one[0])):
		if str(i+1) in refs_dict:
			refs.append(refs_dict[str(i+1)])
		else:
			refs.append("")
	whole_ref = first_one[1].to(last_one[1]).normal()
	chumash = ArrayMapNode()
	chumash.add_title(title_heb[count], "he", primary=True)
	chumash.add_title(title, "en", primary=True)
	chumash.key = title
	chumash.addressTypes = ["Integer"]
	chumash.sectionNames = ["Chapter"]
	chumash.depth = 1
	chumash.wholeRef = whole_ref
	chumash.refs = refs
	chumash.validate()
	perakim["nodes"].append(chumash.serialize())
	f.close()


root = JaggedArrayNode()
root.key = "yalkut_on_torah"
root.add_title("Yalkut Shimoni on Torah", "en", primary=True)
root.add_title(u"ילקות שמעוני על התורה", "he", primary=True)
root.depth = 2
root.sectionNames = ["Remez", "Paragraph"]
root.heSectionNames = [u"רמז", u"פסקה"]
root.addressTypes = ["Integer", "Integer"]


index = {
	"title": "Yalkut Shimoni on Torah",
	"categories": ["Midrash"],
	"alt_structs": {"Parsha": parshiot, "Chapters": perakim},
	"default_struct": "Remez",
	"schema": root.serialize()
}


post_index(index)
