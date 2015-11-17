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



def post_text(ref, text):
    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    url = SEFARIA_SERVER+'/api/texts/'+ref
    values = {'json': textJSON, 'apikey': API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except HTTPError, e:
        print 'Error code: ', e.code
        print e.read()

def post_link(info):
	url = SEFARIA_SERVER+'/api/links/'
	infoJSON = json.dumps(info)
	values = {
		'json': infoJSON, 
		'apikey': API_KEY
	}
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	try:
		response = urllib2.urlopen(req)
		print response.read()
		
	except HTTPError, e:
		print 'Error code: ', e.code


def hasTags(comment):
	tag = re.compile('.*\d+.*')
	match = tag.match(comment)
	if match:
		return True



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
before_dh_dict = {}
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
		if line == "@10" or line == "@60":
			continue
		temp_text += line+" "
		continue_or_not = (line.find("@10") == len_line-3 or line.rfind("@60") == len_line-3 or line.find("@50") == len_line-3)
		continue_or_not = continue_or_not or (line.find("@10") == len_line-4 or line.rfind("@60") == len_line-4 or line.find("@50") == len_line-4)
		continue_or_not = continue_or_not or (line.find("@10") == len_line-5 or line.rfind("@60") == len_line-5 or line.find("@50") == len_line-5)
		if continue_or_not == False:
			continue
		if temp_text.find("@") > 4:
			temp_text = "@28 "+temp_text
		if temp_text.find("@20") >= 0:
			start = temp_text.find("@20")
			end = max(temp_text.find("@30"), temp_text.find("@70"))
			if end == -1:
				print "@20 but not @30/70"
				pdb.set_trace()
			actual_start = temp_text.find("[")
			actual_end = temp_text.find("]")
			if actual_start > start and actual_end < end:
				before_dh = temp_text[start+3:end].replace(temp_text[actual_start:actual_end+1],"")
				daf = temp_text[actual_start:actual_end].replace("[","").replace("]","").replace(" ","")
			daf = convertHebrewToNumber(daf)
			if len(before_dh)>1:
			 if daf in comm_dict:
				before_dh_dict[(daf, len(comm_dict[daf]))] = before_dh
			 else:
				before_dh_dict[(daf, 0)] = before_dh
		if line.find("@28") >= 0:
			start = temp_text.find("@28")
			end = max(temp_text.find("@70"), temp_text.find("@30"))
			before_dh = temp_text[start+3:end]
			if len(before_dh)>1:
			 if daf in comm_dict:
				before_dh_dict[(daf, len(comm_dict[daf]))] = before_dh
			 else:
				before_dh_dict[(daf, 0)] = before_dh
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
			just_added_dh = True
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
			if hasTags(comm) or hasTags(dh) or hasTags(before_dh):
				pdb.set_trace()
			temp_text=""
			if just_added_dh == False:
				dh_dict[daf].append("")
			before_dh = ""
			just_added_dh = False
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
			if hasTags(comm) or hasTags(dh) or hasTags(before_dh):
				pdb.set_trace()
			temp_text=""
			if just_added_dh == False:
				dh_dict[daf].append("")
			before_dh = ""
			just_added_dh = False
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
			if just_added_dh == False:
				dh_dict[daf].append("")
			if hasTags(comm) or hasTags(dh) or hasTags(before_dh):
				pdb.set_trace()
			just_added_dh = False
			before_dh = ""
		temp_text = ""
result = {}
guess = 0
no_guess = 0
result = {}
guess=0
no_guess=0
for daf in dh_dict.keys():
	if len(dh_dict[daf]) != len(comm_dict[daf]):
		pdb.set_trace()
for daf in dh_dict.keys():
	text = get_text("Chullin."+AddressTalmud.toStr("en", daf))
	try:
		match_obj=Match(in_order=True, min_ratio=70, guess=False, range=True, maxLine=len(text)-1)
	except:
		pdb.set_trace()
	dh_arr = []
	for i in range(len(dh_dict[daf])):
		if len(dh_dict[daf][i]) > 0:
			dh_arr.append(dh_dict[daf][i])
	result[daf] = match_obj.match_list(dh_arr, text)
	dh_count = 1
	'''
	if len(dh_dict[daf][i]) == 0, then comm_dict[daf][i] gets added to comm_dict[daf][i-1]+"<br>"
	'''
	for i in range(len(comm_dict[daf])):
		 if (daf, i) in before_dh_dict:
		 	comm_dict[daf][i] = before_dh_dict[(daf, i)]+"<b>"+dh_dict[daf][i]+"</b>"+comm_dict[daf][i]
		 else:
		 	comm_dict[daf][i] = "<b>"+dh_dict[daf][i]+"</b>"+comm_dict[daf][i]
	found = 0
	if len(dh_dict[daf][0]) == 0:
		pdb.set_trace()
	for i in range(len(dh_dict[daf])):
		if len(dh_dict[daf][i]) > 0:
			old_found = found
			found = i
			if found - old_found > 1:
				temp=""
		 		for j in range(found-old_found-1): 
		 			temp+="<br>"+comm_dict[daf][j+old_found+1]
		 		comm_dict[daf][old_found] += temp
	comments = []
	for i in range(len(comm_dict[daf])):
		if len(dh_dict[daf][i])>0:
			comments.append(comm_dict[daf][i])
	#NOW create new array skipping blank ones
	for i in range(len(comm_dict[daf])):
		 if len(dh_dict[daf][i]) > 0:
		 	line_n  = result[daf][dh_count]
		 	dh_count+=1 
		 	if line_n.find("0:")>=0:
		 		no_guess += 1
		 	line_n = line_n.replace("0:", "")
		 	guess+=1
			post_link({
					"refs": [
							"Chullin"+"."+AddressTalmud.toStr("en", daf)+"."+str(line_n), 
							"Rashba on Chullin."+AddressTalmud.toStr("en", daf)+"."+str(i+1)
						],
					"type": "commentary",
					"auto": True,
					"generated_by": "Rashba on Chullin linker",
				 })
	send_text = {
				"versionTitle": "Rashba on Chullin",
				"versionSource": "http://www.sefaria.org",
				"language": "he",
				"text": comments,
				}
	
	post_text("Rashba on Chullin."+AddressTalmud.toStr("en", daf), send_text)
	pdb.set_trace()


print float(guess)/float(guess+no_guess)
print no_guess