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
	
current_perek = 1
current_pasuk = 1
book = sys.argv[1]
current_intro = ""
just_added_intro = False
comments = {}
comments[current_perek] = {}
comments[current_perek][current_pasuk] = []
f = open(book+".txt", "r")
for line in f:
	real_line = line
	line = line.replace("\n", "")
	if line.find("@88")>=0:
		line = line.replace("@88", "")
		current_intro = line
		just_added_intro = True
	elif line.find("@22")>=0:
		line = line.replace("@22", "").replace("(", "").replace(")", "").replace(" ", "").replace('"', '')
		if isGematria(line)==False:
			pdb.set_trace()
		current_pasuk = getGematria(line)
		if current_pasuk in comments[current_perek]:
			pdb.set_trace()
		comments[current_perek][current_pasuk] = []
	elif line.find("@66")>=0:
		prev_perek = current_perek
		line = line.replace("@66", "").replace(" ", "").replace('"', "")
		if isGematria(line)==False:
			pdb.set_trace()
		current_perek = getGematria(line)
		if current_perek < prev_perek:
			pdb.set_trace()
		comments[current_perek] = {}
	if line.find("@11")>=0:
		line = line.replace("@11", "")
		line = line.replace("@33", "")
		if just_added_intro == True:
			comments[current_perek][current_pasuk].append(current_intro)
			just_added_intro = False
		try:
			comments[current_perek][current_pasuk].append(line)
		except:
			pdb.set_trace()
	elif line.find("@44")>=0:
		line = line.replace("@44", "")
		line = line.replace("@55", "")
		if just_added_intro == True:
			comments[current_perek][current_pasuk].append(current_intro)
			just_added_intro = False
		comments[current_perek][current_pasuk].append(line)
	elif line.find("@99")>=0:
		line = line.replace("@99", "")
		comments[current_perek][current_pasuk].append(line)
	prev_line = real_line


param = "off"
for perek in comments:
	last_perek = max(comments.keys())
	for pasuk in comments[perek]:
		send_text = {
				"versionTitle": "Torah Commentary of Yitzchak Abarbanel, Warsaw 1862",
				"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001088711",
				"language": "he",
				"text": comments[perek][pasuk],
				}
		last_pasuk = max(comments[perek].keys())
		if last_pasuk == pasuk and last_perek == perek:
			print "LAST ONE"
			print "****************"
			param = "on"
		post_text("Abarbanel on Torah, "+book+"."+str(perek)+"."+str(pasuk), send_text, param)
		post_link({
				"refs": [
						 book+"."+str(perek)+"."+str(pasuk),
						"Abarbanel on Torah, "+book+"."+str(perek)+"."+str(pasuk)
					],
				"type": "commentary",
				"auto": True,
				"generated_by": "Abarbanel linker",
			 })