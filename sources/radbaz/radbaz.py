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

text = {}
text[1] = {}
text[2] = {}
text[3] = {}
text[4] = {}
text[5] = {}
text[6] = {}
'''
for i in range(6):
	i+=1
	root = JaggedArrayNode()
	root.add_title("Teshuvot HaRadbaz Volume "+str(i), "en", primary=True)
	root.add_title(u'תשובות הרדב"ז חלק '+numToHeb(i), "he", primary=True) 
	print u'תשובות הרדב"ז חלק '+numToHeb(i)
	root.key = str(i)
	root.depth = 2
	root.sectionNames = ["Teshuva", "Paragraph"]
	root.addressTypes = ["Integer", "Integer"]
	root.validate()
	index = {
	"title": "Teshuvot HaRadbaz Volume "+str(i),
    "categories": ["Responsa", "Radbaz"],
    "schema": root.serialize()
	}
	post_index(index)
'''
f = open('radbaz.txt', 'r')
current_teshuva = 0
current_volume = 1
new_vol = True
looking_at_4 = False
for line in f:
	line = line.replace("\n","")
	if line.find("@22")>=0:
		line = line.replace("@22", "")
		if len(line.split(" ")) >= 2 and len(line.split(" ")[1]) > 0:
			if line.find("אלף")>=0:
				current_teshuva = getGematria(line.split(" ")[1]) + 1000
			elif line.find("שני")>=0:
			    current_teshuva = getGematria(line.split(" ")[2]) + 2000
			else:
				current_teshuva = getGematria(line.split(" ")[0])
		else:
			current_teshuva = getGematria(line)
		if current_teshuva == 5 and looking_at_4==True:
			pdb.set_trace()
		text[current_volume][current_teshuva] = []
	elif line.find("@11")>=0:
		if line.find("@33") == -1:
			line = line.replace("@11", "")
		else:
			line = line.replace("@11", "<b>")
			line = line.replace("@33", "</b>")
		text[current_volume][current_teshuva].append(line)
	elif line.find("@91")>=0:
		text[current_volume][current_teshuva].append("["+line.replace("@91", "")+"]")
	elif line.find("@99")>=0:
		text[current_volume][current_teshuva].append("["+line.replace("@99","")+"]")
		current_volume+=1
		if current_volume == 4:
			text[current_volume][current_teshuva] = []
			looking_at_4=True
	prev_line = line

for current_volume in text:
	post_to = "Teshuvot HaRadbaz Volume "+str(current_volume)
	first_value = text[current_volume].keys()[0]
	'''for i in range(first_value):
		i+=1
		send_text = {
				"versionTitle": "Teshuvot HaRadbaz, Warsaw 1882",
				"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001909530",
				"language": "he",
				"text": "",
				}
		post_text(post_to+"."+i, send_text)
	'''
	for current_teshuva in text[current_volume]:
		print current_teshuva
		send_text = {
				"versionTitle": "Teshuvot HaRadbaz, Warsaw 1882",
				"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001909530",
				"language": "he",
				"text": text[current_volume][current_teshuva],
				}
		post_text(post_to+"."+str(current_teshuva), send_text)
		