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
sys.path.insert(0, '../../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	

gematria = {}
gematria['א'] = 1
gematria['ב'] = 2
gematria['ג'] = 3
gematria['ד'] = 4
gematria['ה'] = 5
gematria['ו'] = 6
gematria['ז'] = 7
gematria['ח'] = 8
gematria['ט'] = 9
gematria['י'] = 10
gematria['כ'] = 20
gematria['ל'] = 30
gematria['מ'] = 40
gematria['נ'] = 50
gematria['ס'] = 60
gematria['ע'] = 70
gematria['פ'] = 80
gematria['צ'] = 90
gematria['ק'] = 100
gematria['ר'] = 200
gematria['ש'] = 300
gematria['ת'] = 400

def get_text(ref):
    ref = ref.replace(" ", "_")
    url = 'http://www.sefaria.org/api/texts/'+ref
    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
        data = json.load(response)
        for i, temp_text in enumerate(data['he']):      
			data['he'][i] = data['he'][i].replace(u"\u05B0", "")
			data['he'][i] = data['he'][i].replace(u"\u05B1", "")
			data['he'][i] = data['he'][i].replace(u"\u05B2", "")
			data['he'][i] = data['he'][i].replace(u"\u05B3", "")
			data['he'][i] = data['he'][i].replace(u"\u05B4", "")
			data['he'][i] = data['he'][i].replace(u"\u05B5", "")
			data['he'][i] = data['he'][i].replace(u"\u05B6", "")
			data['he'][i] = data['he'][i].replace(u"\u05B7", "")
			data['he'][i] = data['he'][i].replace(u"\u05B8", "")
			data['he'][i] = data['he'][i].replace(u"\u05B9", "")
			data['he'][i] = data['he'][i].replace(u"\u05BB", "")
			data['he'][i] = data['he'][i].replace(u"\u05BC", "")
			data['he'][i] = data['he'][i].replace(u"\u05BD", "")
			data['he'][i] = data['he'][i].replace(u"\u05BF", "")
			data['he'][i] = data['he'][i].replace(u"\u05C1", "")
			data['he'][i] = data['he'][i].replace(u"\u05C2", "")
			data['he'][i] = data['he'][i].replace(u"\u05C3", "")
			data['he'][i] = data['he'][i].replace(u"\u05C4", "")
        return data['he']
    except:
        print 'Error'

def gematriaFromTxt(txt):
	index=0
	sum=0
	while index <= len(txt)-1:
		if txt[index:index+2] in gematria:
			sum += gematria[txt[index:index+2]]
		index+=1
	return sum

def convertHebrewToNumber(daf):
	try:
		daf_num = gematriaFromTxt(daf.split(",")[0])
	except:
		pdb.set_trace()
	try:
		amud_num = gematriaFromTxt(daf.split(",")[1])
	except:
		pdb.set_trace()
	if amud_num == 1:
		daf = daf_num*2-1
	elif amud_num == 2:
		daf = daf_num*2
	return daf

title="C-B-"
title_option = 1
dh_dict = {}
comm_dict = {}
temp_text = ""
daf=3
for count_file in range(15):
	f = open(title+str(title_option+count_file)+".txt")
	for line in f:
		line=line.replace("\n","")
		len_line = len(line)
		temp_text += line+" "
		if line.find("@99") != len_line-3 and line.find("@99") != len_line-4:
			continue
		if temp_text.find("@") > 4:
			temp_text = "@33 "+temp_text
		if temp_text.find("@01") >= 0:
			start = temp_text.find("@01")
			end = temp_text.find("@09")
			if end == -1:
				print "@01 but not @09"
				pdb.set_trace()
			actual_start = temp_text.find("[")
			actual_end = temp_text.find("]")
			if actual_start > start and actual_end < end:
				daf = temp_text[actual_start:actual_end].replace("[","").replace("]","").replace(" ","")
			daf = convertHebrewToNumber(daf)
			if temp_text.find("@09 @11")>=0:
				temp_text = temp_text.replace("@09 @11","")
		if temp_text.find("@22") >= 0:
			start = temp_text.find("@22")
			end = temp_text.rfind("@11")
			if end == -1:
				print "@22 but not @11"
				pdb.set_trace()
			dh = temp_text[start+3:end]
			if daf in dh_dict:
				dh_dict[daf].append(dh)
			else:
				dh_dict[daf] = []
				dh_dict[daf].append(dh)
		if temp_text.find("@22") >= 0 and (line.find("@33") == -1 or line.find("@33") > 2):
			start = temp_text.find("@22")
			end = temp_text.find("@99")
			if end == -1:
				print "@22 but no end tag"
				pdb.set_trace()
			comm = temp_text[start+3:end]
			if daf in comm_dict:
				comm_dict[daf].append(comm)
			else:
				comm_dict[daf] = []
				comm_dict[daf].append(comm)
			temp_text=""
			continue
		if temp_text.find("@33") >= 0 and temp_text.find("@33") < 2:
			start = temp_text.find("@33")
			end = temp_text.find("@99")
			if end == -1:
				print "@33 but no end tag"
				pdb.set_trace()
			comm = temp_text[start+3:end]
			if daf not in dh_dict:
				dh_dict[daf] = []
			if daf not in comm_dict:
				comm_dict[daf] = []
			comm_dict[daf].append(comm)
		temp_text = ""
result = {}
for daf in dh_dict.keys():
	try:
		text = get_text("Beitzah."+AddressTalmud.toStr("en", daf))
	except:
		pdb.set_trace()
	match_obj=Match(in_order=True, min_ratio=70, guess=False)
	result[daf] = match_obj.match_list(dh_dict[daf], text)

guess = 0
no_guess = 0
for key in result:
	for each_one in result[key]:
		if result[key][each_one][0] == 0:
			no_guess += 1
		else:
			guess += 1
if guess+no_guess > 0:
	print float(guess)/float(guess+no_guess)
