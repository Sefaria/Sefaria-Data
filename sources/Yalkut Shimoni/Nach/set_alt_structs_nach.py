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
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)

from sefaria.model import *

def post_index(index):
	url = SEFARIA_SERVER + '/api/v2/raw/index/Yalkut_Shimoni_on_Nach'
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
	return (perek, Ref("Yalkut Shimoni on Nach."+remez+"."+para))

perakim = {}
perakim = { "nodes" : [] }
parshiot = { "nodes": [] }

title_eng = ["Joshua", "Judges", "I Samuel", "II Samuel", "I Kings", "II Kings", "Isaiah", "Jeremiah", "Ezekiel", "Hosea",
"Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
"Psalms", "Proverbs", "Job", "Song of Songs", "Ruth", "Lamentations", "Ecclesiastes", "Esther", "Daniel", "Ezra", 
"Nehemiah", "I Chronicles", "II Chronicles"] 
title_heb = [u"יהושע", u"שופתים", u"שמואל א", u"שמואל ב", u"מלכים א",
u"מלכים ב", u"ישעיהו", u"ירמיהו", u"יחזקאל", u"הושע", u"יואל", u"עמוס",
u"עובדיה", u"יונה", u"מיכה", u"נחום", u"חבקוק", u"צפניה", u"חגי",
u"זכריה", u"מלאכי", u"תהילים", u"משלי", u"איוב", u"שיר השירים", 
u"רות", u"איכה", u"קהלת", u"אסתר", u"דניאל", u"עזרא", u"נחמיה",
u"דברי הימים א", u"דברי הימים ב"]

def getHebrewParsha(parsha):
	for count, eng in enumerate(title_eng):
		if eng==parsha:
			return title_heb[count]

for count, title in enumerate(title_eng):

	f=open("parsha_"+title+".txt", 'r')
	while True:
		line = f.readline()
		if line == '':
			break
		parsha_name, start_ref = convertIntoRef(line)
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
		if start_perek == end_perek:
			try:
				refs_dict[start_perek] = start_ref.to(end_ref).normal()
			except:
				pdb.set_trace()
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
root.key = "yalkut_on_nach"
root.add_title("Yalkut Shimoni on Nach", "en", primary=True)
root.add_title(u"""ילקות שמעוני על נ״ח""", "he", primary=True)
root.depth = 2
root.sectionNames = ["Remez", "Paragraph"]
root.heSectionNames = [u"רמז", u"פסקה"]
root.addressTypes = ["Integer", "Integer"]



index = {
	"title": "Yalkut Shimoni on Nach",
	"categories": ["Midrash"],
	"alt_structs": {"Chapters": perakim},
	"default_struct": "Remez",
	"schema": root.serialize()
}


post_index(index)
