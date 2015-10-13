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

title="R-7-"
title_option = 1
dh_dict = {}
comm_dict = {}
temp_text = ""
daf=3
for count_file in range(16):
	if title_option+count_file < 10:
		f = open(title+"0"+str(title_option+count_file)+".txt")
	else:
		f = open(title+str(title_option+count_file)+".txt")
	for line in f:
		line=line.replace("\n","")
		len_line = len(line)
		temp_text += line+" "
		if line.find("@10") != len_line-3 and line.find("@60") != len_line-3 and line.find("@50") != len_line-3:
			continue
		if temp_text.find("@") > 4:
			temp_text = "@60 "+temp_text
		if temp_text.find("@20") >= 0:
			start = temp_text.find("@20")
			end = max(temp_text.find("@30"), temp_text.find("@70"))
			if end == -1:
				print "@20 but not @30/70"
				pdb.set_trace()
			actual_start = temp_text.find("[")
			actual_end = temp_text.find("]")
			if actual_start > start and actual_end < end:
				daf = temp_text[actual_start:actual_end].replace("[","").replace("]","").replace(" ","")
			daf = convertHebrewToNumber(daf)
		if temp_text.find("@30") >= 0 or temp_text.find("@70") >= 0:
			start = max(temp_text.find("@30"), temp_text.find("@70"))
			end = temp_text.rfind("@40")
			if end == -1 and temp_text.find("@30")>=0:
				print "@30 but not @40"
				pdb.set_trace()
			dh = temp_text[start+3:end]
			if daf in dh_dict:
				dh_dict[daf].append(dh)
			else:
				dh_dict[daf] = []
				dh_dict[daf].append(dh)
		if temp_text.rfind("@40") >= 0 and (line.find("@60") == -1 or line.find("@60") > 2):
			start = temp_text.rfind("@40")
			end = max(temp_text.find("@10"), temp_text.find("@60"), temp_text.find("@50"))
			if end == -1:
				print "@40 but no end tag"
				pdb.set_trace()
			comm = temp_text[start+3:end]
			if daf in comm_dict:
				comm_dict[daf].append(comm)
			else:
				comm_dict[daf] = []
				comm_dict[daf].append(comm)
			temp_text=""
			continue
		if temp_text.find("@70") >= 0:
			start = temp_text.find("@70")
			end = max(temp_text.find("@10"), temp_text.find("@60"), temp_text.find("@50"))
			if end == -1:
				print "@70 but no end tag"
				pdb.set_trace()
			comm = temp_text[start+3:end]
			if daf in comm_dict:
				comm_dict[daf].append(comm)
			else:
				comm_dict[daf] = []
				comm_dict[daf].append(comm)
			temp_text=""
			continue
		if temp_text.find("@60") >= 0 and temp_text.find("@60") < 2:
			start = temp_text.find("@60")
			end = max(temp_text.find("@60"), temp_text.find("@10"), temp_text.find("@50"))
			if end == -1:
				print "@60 but no end tag"
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
	text = get_text("Chullin."+AddressTalmud.toStr("en", daf))
	match_obj=Match(in_order=True, min_ratio=70, guess=False)
	if text==None:
		print daf
	if text!=None:
		result[daf] = match_obj.match_list(dh_dict[daf], text)

guess = 0
no_guess = 0
for key in result:
	for each_one in result[key]:
		if result[key][each_one][0] == 0:
			no_guess += 1
		else:
			guess += 1
print float(guess)/float(guess+no_guess)
print no_guess
pdb.set_trace()