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
from functions import *
import unittest


sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	

root = JaggedArrayNode()
root.key = 'footnotes'
root.add_title("Footnotes to Kohelet by Bruce Heitler", "en", primary=True)
root.add_title(u"הערות לקהלת", "he", primary=True)
root.sectionNames = ["Chapter", "Footnote"]
root.addressTypes = ["Integer", "Integer"]
root.depth = 2
root.validate()
index = {
    "title": "Footnotes to Kohelet by Bruce Heitler",
    "categories": ["Modern Works", "Tanach", "Writings", "Ecclesiastes"],
    "schema": root.serialize()
}
post_index(index)

text = []
chapter = -1
footnotes = []
f=open('withnumbers.txt', 'r')
count = 0
for line in f:
	line = line.replace('\n', '')
	if len(line.replace(" ", ""))>5:
		if line.find("Chapter")>=0 and len(line.split(" "))<5:
			chapter+=1
			footnotes.append([])
		else:
			count+=1
			words = line.split(" ")
			not_abc = re.compile('\d+[^a-zA-Z]+')
			if not_abc.match(line):
				line = line.replace(not_abc.match(line).group(0), "")
			if count > 48:
				pdb.set_trace()
			footnotes[chapter].append(line)

f.close()
send_text = {
				"versionTitle": "Footnotes to Kohelet by Bruce Heitler",
				"versionSource": "http://www.kohelet.org",
				"language": "en",
				"text": footnotes,
				}		
post_text("Footnotes to Kohelet by Bruce Heitler", send_text, "on")

text=[]
chapter = -1
f = open("heitler kohelet.txt", 'r')
for line in f:
	line = line.replace("\n", "")
	line = line.replace("\r", "")
	if line.find("Chapter")>=0 and len(line.split(" "))<5:
		print line
		text.append([])
		chapter+=1
	elif len(line.replace(" ",""))>0:
		number = line.split("\t")[0]
		try:
			verse = int(number)
			line = line.replace("\t", "")
			line = line.replace(number, "")
			text[chapter].append(line)
		except:
			last_one = len(text[chapter])-1
			text[chapter][last_one] += "<br>"+line
f.close()
send_text = {
				"versionTitle": "Kohelet by Bruce Heitler",
				"versionSource": "http://www.kohelet.org",
				"language": "en",
				"text": text,
				}
post_text("Kohelet", send_text, "on")