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
sys.path.insert(0, '../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	

root = SchemaNode()
root.add_title("Brit Moshe", "en", primary=True)
root.add_title(u"ברית משה", "he", primary=True)
root.key = "britmoshe"


vol1 = JaggedArrayNode()
vol1.key = 'vol1'
vol1.add_title("Volume One", "en", primary=True)
vol1.add_title(u"חלק "+numToHeb(1), "he", primary=True)
vol1.depth = 3
vol1.sectionNames = ["Mitzvah", "Comment", "Paragraph"]
vol1.addressTypes = ["Integer", "Integer", "Integer"]




vol2 = JaggedArrayNode()
vol2.key = 'vol2'
vol2.add_title("Volume Two", "en", primary=True)
vol2.add_title(u"חלק "+numToHeb(2), "he", primary=True)
vol2.depth = 3
vol2.sectionNames = ["Mitzvah", "Comment", "Paragraph"]
vol2.addressTypes = ["Integer", "Integer", "Integer"]



root.append(vol1)
root.append(vol2)
root.validate()
index = {
	"title": "Brit Moshe",
	"categories": ["Commentary2", "Halakhah", "Sefer Mitzvot Gadol"],
	"schema": root.serialize()
	}
post_index(index)
f = open("Brit Moshe vol 1.txt", 'r')
current_mitzvah = 1
text = {}
text[current_mitzvah] = []
comment = -1
prev_line = ""
for line in f:
	actual_line = line
	line=line.replace("\n","")
	if line.find("@22")>=0:
		line = line.replace(")","").replace(" ","")
		new_comment = getGematria(line)
		if new_comment < comment + 1:
			print 'new comment < comment +1'
			pdb.set_trace()
		if len(text[current_mitzvah]) != comment+1:
			print 'len != comment'
			pdb.set_trace()
		for i in range(new_comment-len(text[current_mitzvah])):
			text[current_mitzvah].append([])
			comment = len(text[current_mitzvah])-1
			try:
				text[current_mitzvah][comment] = []
			except:
				print 'cant add'
				pdb.set_trace()
	elif line.find("@88מצוה לא תעשה ")>=0:
		pos = len("@88מצוה לא תעשה ")
		line = line[pos:].replace("'","").replace('"', '')
		if actual_line.find("עד")>=0:
			beg, end = line.split("עד")
			beg = getGematria(beg)
			end = getGematria(end)
			if end <= beg:
				pdb.set_trace()
			all = ""
			for i in range(end-beg):
				text[i+beg] = []
				text[i+beg].append([])
				text[i+beg][0].append(u"ראו מצוה "+str(end))
				if i==end-beg-1:
					all += str(i+beg)
				else:
					all += str(i+beg)+", "
			text[end] = []
			text[end].append([])
			text[end][0].append(u"מצוות "+all)
			current_mitzvah = end
			comment = 0
		elif len(line.split(" ")) == 3:
			print line
			mitzvah_one = getGematria(line.split(" ")[0])
			mitzvah_two = getGematria(line.split(" ")[1])
			text[mitzvah_one] = []
			text[mitzvah_two] = []
			text[mitzvah_one].append([])
			text[mitzvah_two].append([])
			text[mitzvah_one][0].append(u"ראו מצוה "+str(mitzvah_two))
			text[mitzvah_two][0].append(u"מצוות "+str(mitzvah_one)+u" ו"+str(mitzvah_two))
			current_mitzvah = mitzvah_two
			comment = 0
		else:
			current_mitzvah = getGematria(line)
			text[current_mitzvah] = []
			comment = -1
	else:
		if line.find("@33")==-1 and line.find("@11")>=0:
			pdb.set_trace()
		line = line.replace("@00","").replace("@99","")
		line = line.replace("@11", "<b>")
		line = line.replace("@33", "</b>")
		line = line.replace("@66", "").replace("@55","").replace("@44","")
		text[current_mitzvah][comment].append(line)
	prev_line = actual_line
			
for mitzvah in text:
	send_text = {		
		"versionTitle":  "Munkatch, 1901",
		"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637",
		"text": text[mitzvah],
		"language": "he"
		}
	post_text("Brit Moshe, Volume One."+str(mitzvah), send_text)
	post_link({
				"refs": [
						 "Brit Moshe, Volume One."+str(mitzvah)+".1",
						"Sefer Mitzvot Gadol, Volume One."+str(mitzvah)
					],
				"type": "commentary",
				"auto": True,
				"generated_by": "Brit Moshe to SEMAG linker"
			 })
