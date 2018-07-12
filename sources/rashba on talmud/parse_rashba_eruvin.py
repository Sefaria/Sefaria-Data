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

errors = open('errors.html', 'w')

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


def post_text(ref, text, index_count="off"):
    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    if index_count == "off":
    	url = SEFARIA_SERVER+'api/texts/'+ref+'?count_after=0'
    else:
    	url = SEFARIA_SERVER+'api/texts/'+ref
    values = {'json': textJSON, 'apikey': API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
    	response = urllib2.urlopen(req)
        x= response.read()
        print x
        if x.find("error")>=0 and x.find("Line")>=0 and x.find("0")>=0:
			pdb.set_trace()
    except HTTPError, e:
        errors.write(e.read())

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

def replaceBadTags(temp_text):
	temp_text = temp_text.replace("@98@77", "@70")
	temp_text = temp_text.replace("@77@30", "@30")
	temp_text = temp_text.replace("@77@20", "@20")
	temp_text = temp_text.replace("@77@70", "@70")
	temp_text = temp_text.replace("@77", "@70")

	temp_text = temp_text.replace("@98", "")
	temp_text = temp_text.replace("05", "60")
	temp_text = temp_text.replace("@65@40", "")
	temp_text = temp_text.replace("@65", "")
	if temp_text.find("@28@60")>=0:
		temp_text = temp_text.replace("@28@60", "@60")
	elif temp_text.find("@60@28")>=0:
		temp_text = temp_text.replace("@60@28", "")
	elif temp_text.find("@70@28")>=0:
		temp_text = temp_text.replace("@70@28","@70")
	elif temp_text.find("@28@70")>=0:
		temp_text=temp_text.replace("@28@70", "@70")
	elif temp_text.find("@28@20")>=0:
		temp_text=temp_text.replace("@28@20", "@20")
	temp_text = temp_text.replace("@04", "")
	temp_text = temp_text.replace("@14", "")
	temp_text = temp_text.replace("@30@40", "")
	temp_text = temp_text.replace("@40@20", "@20")
	temp_text = temp_text.replace("@89@40", "")
	temp_text = temp_text.replace("@30@40", "")
	temp_text = temp_text.replace("@40@20", "@20")
	temp_text = temp_text.replace("@00", "@28")
	temp_text = temp_text.replace("#1121.", "@60")
	temp_text = temp_text.replace("#1121", "@60")
	temp_text = temp_text.replace("@28@10", "@10")
	if temp_text.find("@40") != -1 and temp_text.rfind("@40") != -1 and temp_text.find("@40") != temp_text.rfind("@40"):
		temp_text = removeSecond40(temp_text)
	if temp_text.find("@") > 4:
			if temp_text.find("@") != temp_text.rfind("@"):
				temp_text = "@28 "+temp_text
			else:
				temp_text = "@60 "+temp_text
	if temp_text.find("@10") != temp_text.rfind("@10"):
		temp_text = temp_text.replace("@10", "")
		temp_text = temp_text + "@10"
	return temp_text
	
masechet = str(sys.argv[1])
if len(sys.argv) == 3:
	masechet += " "+sys.argv[2]
title="R-"
title_option = 13
dh_dict = {}
before_dh_marker = "@28" #@00
before_dh_dict = {}
comm_dict = {}
temp_text = ""
before_dh=""
just_added_dh = False
dh=""
daf=3
titles = ["2RSB07-", "2RSB08-", "2RSB09-", "2RSB10-", "2RSB11-", "2RSB12-"]
for title in titles:
  if title == "2RSB09-":
    this_range = 5
  elif title == "2RSB12-":
    this_range = 1
  else:
  	this_range = 6  
  for count_file in range(this_range):
	lines = []
	f = open(masechet+"/"+title+str(count_file+1)+".txt")
	for line in f:
		line=line.replace("\n","")
		line =line.replace("@05","@60")
		text = line
		while text.find("@10 @60")>=0:
			loc = text.find("@10 @60")
			lines.append(text[0:loc+3])
			text = text[loc+4:]
		lines.append(text)
	for line in lines:
		line=line.replace("\n","")
		len_line = len(line)
		if line == "@10" or line=="@60" or line=="@50":
			continue
		temp_text += line+" "
		continue_or_not = False
		for i in range(5):
			j=i+2
			if len_line >= j:
				continue_or_not = continue_or_not or (line.find("@10") == len_line-j or line.rfind("@60") == len_line-j or line.find("@50") == len_line-j)	
		if continue_or_not == False:
			continue
		temp_text = replaceBadTags(temp_text)
		if temp_text.find("@20") >= 0:
			start = temp_text.find("@20")
			end = max(temp_text.find("@30"), temp_text.find("@70"))
			if end == -1:
				end = temp_text.find("@10")
				if end == -1:
					print "@20 but not end tag"
					pdb.set_trace()
			actual_start = temp_text.find("[")
			actual_end = temp_text.find("]")
			if actual_start > start and actual_end < end:
				before_dh = temp_text[start+3:end].replace(temp_text[actual_start:actual_end+1],"")
				daf = temp_text[actual_start:actual_end].replace("[","").replace("]","").replace(" ","")
			daf = convertHebrewToNumber(daf)
			if isinstance(daf, basestring):
				print "********"
				pdb.set_trace()
			if len(before_dh)>1:
			 if daf in comm_dict:
				before_dh_dict[(daf, len(comm_dict[daf]))] = before_dh
			 else:
				before_dh_dict[(daf, 0)] = before_dh
			if hasTags(before_dh):
				pdb.set_trace()
		if temp_text.find("@28") >= 0:
			start = temp_text.find("@28")
			end = max(temp_text.find("@70"), temp_text.find("@30"))
			before_dh = temp_text[start+3:end]
			if len(before_dh)>1:
			 if daf in comm_dict:
				before_dh_dict[(daf, len(comm_dict[daf]))] = before_dh
			 else:
				before_dh_dict[(daf, 0)] = before_dh
			if hasTags(before_dh):
				pdb.set_trace()
		if (temp_text.find("@30") >= 0 or temp_text.find("@70") >= 0) and temp_text.rfind("@40")>=0:
			start = max(temp_text.find("@30"), temp_text.find("@70"))
			end = temp_text.rfind("@40")
			if end == -1:
				print "@30 but not end tag"
				pdb.set_trace()
			dh = temp_text[start+3:end]
			if daf in dh_dict:
				dh_dict[daf].append(dh)
			else:
				dh_dict[daf] = []
				dh_dict[daf].append(dh)
			if hasTags(dh):
				pdb.set_trace()
			just_added_dh = True
		if temp_text.rfind("@40") >= 0 and (temp_text.find("@60") == -1 or temp_text.find("@60") > 3):
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
			if just_added_dh == False:
				dh_dict[daf].append("")
			if hasTags(comm) or hasTags(dh) or hasTags(before_dh):
				pdb.set_trace()
			temp_text=""
			before_dh =""
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
			if not daf in dh_dict:
				dh_dict[daf] = []
			if just_added_dh == False:
				dh_dict[daf].append("")
			if hasTags(comm) or hasTags(dh) or hasTags(before_dh):
				pdb.set_trace()
			before_dh =""
			just_added_dh = False
			temp_text=""
			continue
		if temp_text.find("@60") >= 0 and temp_text.find("@60") < 4:
			temp_text = temp_text.replace("@40", "")
			start = temp_text.find("@60")
			end = max(temp_text.rfind("@60"), temp_text.find("@10"), temp_text.find("@50"))
			if end == -1:
				print "@60 but no end tag"
				pdb.set_trace()
			comm = temp_text[start+3:end]
			if daf not in dh_dict:
				dh_dict[daf] = []
			if daf not in comm_dict:
				comm_dict[daf] = []
			comm_dict[daf].append(comm)
			if hasTags(comm) or hasTags(dh) or hasTags(before_dh):
				pdb.set_trace()
			if just_added_dh == False:
				dh_dict[daf].append("")
			just_added_dh = False
		before_dh =""
		temp_text = ""
result = {}
guess=0
no_guess=0
for daf in dh_dict.keys():
	if len(dh_dict[daf]) != len(comm_dict[daf]):
		pdb.set_trace()
for daf in dh_dict.keys():
	last_one = max(dh_dict.keys())
	text = get_text(masechet+"."+AddressTalmud.toStr("en", daf))
	try:
		match_obj=Match(in_order=True, min_ratio=77, guess=False, range=True)
	except:
		pdb.set_trace()
	dh_arr = []
	for i in range(len(dh_dict[daf])):
		if len(dh_dict[daf][i]) > 0:
			dh_arr.append(dh_dict[daf][i])
	try:
		result[daf] = match_obj.match_list(dh_arr, text, masechet+" "+AddressTalmud.toStr("en", daf))
	except:
		pdb.set_trace()
	for i in range(len(comm_dict[daf])):
		 if (daf, i) in before_dh_dict:
		 	comm_dict[daf][i] = before_dh_dict[(daf, i)]+"<b>"+dh_dict[daf][i]+"</b>"+comm_dict[daf][i]
		 else:
		 	comm_dict[daf][i] = "<b>"+dh_dict[daf][i]+"</b>"+comm_dict[daf][i]
	found = 0
	first_real_dh = -1
	for i in range(len(dh_dict[daf])):
		if len(dh_dict[daf][i]) > 0:
			if i==0:
				first_real_dh = i
			if first_real_dh == -1 and i > 0:
				first_real_dh = i
				prepend = ""
				for j in range(i):
					prepend += comm_dict[daf][j]+"<br>"
				orig = comm_dict[daf][i]
				comm_dict[daf][i] = prepend + orig
			old_found = found
			found = i
			if found - old_found > 1:
				temp=""
		 		for j in range(found-old_found-1): 
		 			temp+="<br>"+comm_dict[daf][j+old_found+1]
		 		comm_dict[daf][old_found] += temp
		elif i == len(dh_dict[daf])-1:
		 	if i - found >= 1:
				temp=""
		 		for j in range(i-found): 
		 			temp+="<br>"+comm_dict[daf][j+found+1]
		 		comm_dict[daf][found] += temp
	comments = []
	for i in range(len(comm_dict[daf])):
		if len(dh_dict[daf][i])>0:
			comments.append(comm_dict[daf][i])
	send_text = {
				"versionTitle": "Rashba on "+masechet,
				"versionSource": "http://www.sefaria.org",
				"language": "he",
				"text": comments,
				}
	if daf == last_one:
		post_text("Rashba on "+masechet+"."+AddressTalmud.toStr("en", daf), send_text, "on")
	else:
		post_text("Rashba on "+masechet+"."+AddressTalmud.toStr("en", daf), send_text)
	for i in range(len(comments)):
		line_n  = result[daf][i+1]
		if line_n.find("0:")>=0:
			no_guess += 1
		line_n = line_n.replace("0:", "")
		guess+=1
		post_link({
				"refs": [
						 masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(line_n), 
						"Rashba on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(i+1)
					],
				"type": "commentary",
				"auto": True,
				"generated_by": "Rashba on "+masechet+" linker",
			 })
		
print float(guess)/float(guess+no_guess)
print no_guess
