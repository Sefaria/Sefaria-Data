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

text={}
perek_reg_exp = re.compile('.*@\d+\.?')
title = "Rashi on "+sys.argv[1]
f = open("English "+title+"_rev.txt",'r')
for line in f:
	if perek_reg_exp.match(line) is None:
		pdb.set_trace()
	perek = perek_reg_exp.match(line).group(0)
	pos_at = perek.find("@")
	perek = perek[pos_at+1:]
	try:
		perek = int(perek.replace(".",""))
	except:
		pdb.set_trace()
	if perek in text:
		pdb.set_trace()
	text[perek] = {}
	line = line.replace(perek_reg_exp.match(line).group(0),"")
	pasuk_markers = re.findall('\(\d+\)', line)
	passukim = re.split('\(\d+\)', line)
	if len(passukim[0].replace(" ", "")) > 0:
		pdb.set_trace()
	if len(passukim) != len(pasuk_markers)+1:
		pdb.set_trace()
	for count, pasuk_marker in enumerate(pasuk_markers):
		pasuk_marker = int(pasuk_marker.replace(")","").replace("(",""))
		text[perek][pasuk_marker] = []
		comments = passukim[count+1].split("#")
		for comment in comments:
			text[perek][pasuk_marker].append(comment)
	text[perek] = convertDictToArray(text[perek])
			
text = convertDictToArray(text)

send_text = {
		"versionTitle":  "Pentateuch with Rashi's commentary by M. Rosenbaum and A.M. Silbermann",
		"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001969084",
		"text": text,
		"language": "en"
	}
post_text(title, send_text)

		
	
	
	