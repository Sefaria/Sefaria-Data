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
        for i, line in enumerate(data['he']):      
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


def removeSecond40(line):
	arr = line.split(" ")
	found_40 = False
	new_line = ""
	for i in range(len(arr)):
		if found_40 == False or arr[i].find("@40")==-1:
			new_line += arr[i] + " "
		elif arr[i].find("@10")>=0 or arr[i].find("@60")>=0:
			new_line += arr[i].replace("@30","").replace("@40","") + " "		
		if arr[i].find("@40") >= 0:
			found_40 = True
	return new_line
	


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

title="R-C-K-"
title_option = 1
dh_dict = {}
comm_dict = {}
line = ""
before_dh_dict = {}
daf=3
for count_file in range(15):
	if title_option+count_file < 10:
		f = open(title+"0"+str(title_option+count_file)+".txt")
	else:
		f = open(title+str(title_option+count_file)+".txt")
	lines = []
	for line in f:
		line=line.replace("\n","")
		text = line
		while text.find("@10 @60")>=0:
			loc = text.find("@10 @60")
			lines.append(text[0:loc+3])
			text = text[loc+4:]
		lines.append(text)
	for line in lines:
		line = removeSecond40(line)
		if line.find("@") > 4:
			line = "@28 "+line
		line = line.replace("@30@40", "")
		line = line.replace("@40@20", "@20")
		if line.find("@20") >= 0:
			start = line.find("@20")
			end = max(line.find("@30"), line.find("@70"))
			if end == -1:
				print "@20 but not @30/70"
				pdb.set_trace()
			actual_start = line.find("[")
			actual_end = line.find("]")
			if actual_start > start and actual_end < end:
				before_dh = line[start+3:end].replace(line[actual_start:actual_end+1],"")
				daf = line[actual_start:actual_end].replace("[","").replace("]","").replace(" ","")
			daf = convertHebrewToNumber(daf)
			if len(before_dh)>1:
			 if daf in comm_dict:
				before_dh_dict[(daf, len(comm_dict[daf]))] = before_dh
			 else:
				before_dh_dict[(daf, 0)] = before_dh
		if line.find("@28") >= 0:
			start = line.find("@28")
			end = max(line.find("@70"), line.find("@30"))
			before_dh = line[start+3:end]
			if len(before_dh)>1:
			 if daf in comm_dict:
				before_dh_dict[(daf, len(comm_dict[daf]))] = before_dh
			 else:
				before_dh_dict[(daf, 0)] = before_dh
		if (line.find("@30") >= 0 or line.find("@70") >= 0) and line.rfind("@40")>=0:
			start = max(line.find("@30"), line.find("@70"))
			end = line.rfind("@40")
			if end == -1 and line.find("@30")>=0:
				print "@30 but not @40"
				pdb.set_trace()
			dh = line[start+3:end]
			if daf in dh_dict:
				dh_dict[daf].append(dh)
			else:
				dh_dict[daf] = []
				dh_dict[daf].append(dh)
			just_added_dh = True
		if line.find("@40") >= 0 and (line.find("@60") == -1 or line.rfind("@60") > 2):
			start = line.find("@40")
			end = max(line.find("@10"), line.rfind("@60"), line.find("@50"))
			if end == -1:
				print "@40 but no end tag"
				pdb.set_trace()
			comm = line[start+3:end]
			if daf in comm_dict:
				comm_dict[daf].append(comm)
			else:
				comm_dict[daf] = []
				comm_dict[daf].append(comm)
			if just_added_dh == False:
				dh_dict[daf].append("")
			if hasTags(comm) or hasTags(dh) or hasTags(before_dh):
				pdb.set_trace()
			just_added_dh = False
			continue
		if line.find("@70") >= 0:
			start = line.find("@70")
			end = max(line.find("@10"), line.find("@60"), line.find("@50"))
			if end == -1:
				print "@70 but no end tag"
				pdb.set_trace()
			comm = line[start+3:end]
			if daf in comm_dict:
				comm_dict[daf].append(comm)
			else:
				comm_dict[daf] = []
				comm_dict[daf].append(comm)
			if just_added_dh == False:
				dh_dict[daf].append("")
			just_added_dh = False
			if hasTags(comm) or hasTags(dh) or hasTags(before_dh):
				pdb.set_trace()
			continue
		if line.find("@60") >= 0 and line.find("@60") < 2:
			start = line.find("@60")
			end = max(line.rfind("@60"), line.find("@10"), line.find("@50"))
			if end == -1:
				print "@60 but no end tag"
				pdb.set_trace()
			comm = line[start+3:end]
			comm = comm.replace("@40","")
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
result = {}
guess=0
no_guess=0
for daf in dh_dict.keys():
	if len(dh_dict[daf]) != len(comm_dict[daf]):
		pdb.set_trace()
for daf in dh_dict.keys():
	text = get_text("Ketubot."+AddressTalmud.toStr("en", daf))
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
							"Ketubot"+"."+AddressTalmud.toStr("en", daf)+"."+str(line_n), 
							"Rashba on Ketubot."+AddressTalmud.toStr("en", daf)+"."+str(i+1)
						],
					"type": "commentary",
					"auto": True,
					"generated_by": "Rashba on Ketubot linker",
				 })
	send_text = {
				"versionTitle": "Rashba on Ketubot",
				"versionSource": "http://www.sefaria.org",
				"language": "he",
				"text": comments,
				}
	
	post_text("Rashba on Ketubot."+AddressTalmud.toStr("en", daf), send_text)
	pdb.set_trace()


print float(guess)/float(guess+no_guess)
print no_guess