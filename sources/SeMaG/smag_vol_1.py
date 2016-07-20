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

files = ["Semag Vol 1.txt", "Semag Vol 2.txt"]
'''
short_lines = open('short_lines.txt', 'w')
for file_name in files:
	file = open(file_name, 'r')
	for line in file:
		line = line.replace("\n","")
		if len(line.split(" "))<8 and len(line)>0 and line.find("@11")==-1 and line.find("@00")==-1:
			line = line.replace("'","").replace("@22","").replace("@00","").replace('"',"")
			if not isGematria(line.split(" ")[0]):
				short_lines.write(line+"\n")
		prev_line = line
'''
def addMitzvah(mitzvah, text):
	if not isGematria(mitzvah):
		print 'not gematria!'
		pdb.set_trace()
	current_mitzvah = getGematria(mitzvah)
	if current_mitzvah in text:
		print "double mitzvah"
		pdb.set_trace()
	return current_mitzvah
	


smag = open(files[0],'r')
current_mitzvah = 0
tag = re.compile('@\d+')
text = {}
header = ""
how_many_blank = 0
for line in smag:
	line = line.replace("\n","")
	line = line.replace("@55", "").replace("@44", "").replace("@33","").replace("@66","")
	if line.find("@11")>=0:
		words = line.split(" ")
		for count, word in enumerate(words):
			if tag.match(word):
				words[count] = words[count].replace(tag.match(word).group(0),"")
		words = " ".join(words)
		msg = ""
		for each_one in range(how_many_blank):
			msg += str(current_mitzvah-(how_many_blank-each_one))+", "
			text[current_mitzvah-(each_one+1)].append(u"מצוה ראו "+str(current_mitzvah))
		if how_many_blank > 0:
			text[current_mitzvah].append(u"מצוות "+u" "+msg+str(current_mitzvah))
			how_many_blank = 0
		text[current_mitzvah].append(words)
	elif line.find("@22")>=0:
		line = line.replace("@22","").replace(".","").replace("'","").replace('"','')
		if line[len(line)-1]==" ":
			line = line[:len(line)-1]
		if len(line.split(" ")) == 1:
			how_many_blank = 0
			current_mitzvah = addMitzvah(line, text)
			text[current_mitzvah] = []
			if len(header)>0:
				print header
				text[current_mitzvah].append(header)
		elif len(line.split(" "))>1:
			mitzvot = line.split(" ")
			how_many_blank = len(mitzvot)-1
			for m_count, mitzvah in enumerate(mitzvot):
				current_mitzvah = addMitzvah(mitzvah, text)
				text[current_mitzvah] = []
				if m_count == 0 and len(header)>0:
					print header
					text[current_mitzvah].append(header)
		else:
			print 'another case not considered'
			pdb.set_trace()
		header = ""
	elif line.find("@00")>=0:
		header = line.replace("@00","")
	prev_line = line
	
text = convertDictToArray(text)
send_text = {
		"versionTitle": "Munkatch, 1901",
		"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637",
		"language": "he",
		"text": text,
	}
post_text("Sefer Mitzvot Gadol, Volume One", send_text, "on")

heb_nodes = [u"הלכות עירובין", u"הלכות אבילות", u"הלכות תשעה באב", u"הלכות מגילה", u"הלכות חנוכה"]
eng_nodes = ["Laws of Eruvin", "Laws of Mourning", "Laws of Tisha B'Av", "Laws of Megillah", "Laws of Chanukah"]

appendix = open('appendix.txt','r')
node=0
title=""
text={}
for line in appendix:
	if node < 5 and line.find(heb_nodes[node].encode('utf-8'))==0:
		title = eng_nodes[node]
		print title
		node+=1
	if not line.find(heb_nodes[node-1].encode('utf-8'))==0 and len(line.split(" "))>1:
		if title not in text:
			text[title] = []
		text[title].append(line)

for title in text:
	send_text = {
		"versionTitle": "Munkatch, 1901",
		"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637",
		"language": "he",
		"text": text[title],
	}
	post_text("Sefer Mitzvot Gadol, Volume Two, "+title, send_text, "on")