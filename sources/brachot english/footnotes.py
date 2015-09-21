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
from sefaria.model.schema import AddressTalmud	
def post_text(ref, text):
    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    url = SEFARIA_SERVER+'api/texts/'+ref
    values = {'json': textJSON, 'apikey': API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except HTTPError, e:
        print 'Error code: ', e.code
        print e.read()
def get_text(ref):
 	ref = ref.replace(" ", "_")
 	url = 'http://www.sefaria.org/api/texts/'+ref
 	req = urllib2.Request(url)
 	try:
 		response = urllib2.urlopen(req)
 		data = json.load(response)
 		return data
 	except: 
 		return 'Error'
 
footnotes = []
filenames = ["BT_Chapter I Footnotes.txt", "BT_Chapter II Footnotes.txt", "BT_Chapter III Footnotes.txt", "BT_Chapter IV Footnotes.txt",
"BT_Chapter V Footnotes.txt", "BT_Chapter VI Footnotes.txt", "BT_Chapter VII Footnotes.txt", "BT_Chapter VIII Footnotes.txt",
"BT_Chapter IX Footnotes.txt"]
is_a_num = re.compile('\d+')
log_file = open('log_Footnotes.txt', 'w')
for filename in filenames:
	file = open(filename)
	for line in file:
		line = line.replace("\n", "")
		line = line.replace("\r", "")
		first_word = line.split(" ")[0]
		if first_word == "Page:":	
			page_num = line.split(" ")[1]
		if line.find("***") >= 0:
			log_file.write('Found Hebrew characters on page '+str(page_num)+'\n')
		match = is_a_num.match(first_word)
		if match:
			footnotes.append(line)
footnotes_per_line = {}
footnote=0
title_comm = "Footnotes on Berakhot"
for i in range(124):
	j = i + 3
	text = get_text("Berakhot."+AddressTalmud.toStr("en", j))['text']
	for line_n, line in enumerate(text):
		p = re.compile('\[\d+\]')
		words = line.split(" ")
		for word in words:
			match = p.match(word)
			if match:
				number = match.group(0).replace("[","").replace("]","")
				comment = footnotes[footnote] 
				footnote+=1
				if (line_n, j) in footnotes_per_line:
					footnotes_per_line[(line_n, j)]+=1
				else:
					footnotes_per_line[(line_n, j)]=1
				text = {
				"versionTitle": "",
				"versionSource": "",
				"language": "he",
				"text": comment,
				}
				pdb.set_trace()
				post_text(title_comm+"."+AddressTalmud.toStr("en", j)+"."+str(line_n)+"."+str(footnotes_per_line[(line_n,j)]), text)