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
	
smag = open("Semag Vol 2.txt",'r')
current_mitzvah = 0
tag = re.compile('@\d+')
text = {}
prev_line=""
msg=""
header=""
for line in smag:
	line = line.replace('\n', '')
	if line.find("הלכות")>=0 and len(line.split(" "))<7:
		header = line
		continue
	if len(line.split(" ")) == 1:
		how_many_blank = 0
		line = line.replace(".","").replace("'","").replace('"','')
		if line[len(line)-1]==" ":
			line = line[:len(line)-1]
		current_mitzvah = addMitzvah(line, text)
		text[current_mitzvah] = []
		if len(header)>0:
			text[current_mitzvah].append(header)
			header = ""
	elif line.find("רמד רמה רמו")>=0:
		how_many_blank = 2
		mitzvot = line.split(" ")
		for m_count, mitzvah in enumerate(mitzvot):
			current_mitzvah = addMitzvah(mitzvah, text)
			text[current_mitzvah] = []	
			if len(header)>0 and m_count==0:
				text[current_mitzvah].append(header)
				header = ""
	else:
		for each_one in range(how_many_blank):
			msg += str(current_mitzvah-(how_many_blank-each_one))+", "
			text[current_mitzvah-(each_one+1)].append(u"ראו מצוה "+str(current_mitzvah))
		if how_many_blank > 0:
			text[current_mitzvah].append(u"מצוות "+msg+str(current_mitzvah))
			how_many_blank = 0
		text[current_mitzvah].append(line)
	prev_prev_line = prev_line
	prev_line = line
	
text = convertDictToArray(text)
send_text = {
		"versionTitle": "Munkatch, 1901",
		"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637",
		"language": "he",
		"text": text,
	}	
post_text("Sefer Mitzvot Gadol, Volume Two", send_text, "on")
	