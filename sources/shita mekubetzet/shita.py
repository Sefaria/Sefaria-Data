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
import unittest


sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	


title = "BZHR"
start_title = 1
if len(sys.argv)>2:
	masechet = sys.argv[1]+" "+sys.argv[2]
else:
	masechet = sys.argv[1]
end = "@01"
num_files = 11
current_text = ""
current_daf = 3
dh_dict = {}
comm_dict = {}
second_time = False

def convertDaf(daf_info):
	daf_info = daf_info.replace("'", '')
	daf_info = daf_info.replace(" ", "")
	daf_info = daf_info.replace('"', '')
	return daf_info

def parse(text):
	global current_daf
	amud_written_out = False
	tags = ["@07", "@06", "@05", "@04", "@08", "@24", "@14", "@33", "@09", "@02"]
	first_at = text.find("@")
	if first_at >=0:
		text = text[first_at:]
	text = text.replace("@05@04", "@06")
	text = text.replace("@19", "@06")
	if text.find("08") != text.rfind("08"):
		print "TWO 08s"
		pdb.set_trace()
	if text.find("@08דף")>=0:
		words = text.split(" ")
		daf_pos = -1
		for count, word in enumerate(words):
			if word.find("@08דף")>=0:
				daf_pos = count
				break
		daf = words[daf_pos+1].replace("@06", "")
		daf = getGematria(convertDaf(daf))
		amud = words[daf_pos+2]
		if amud.find('עמוד')>=0:
			amud = words[daf_pos+3]
			amud_written_out = True
		if amud.find('ע"ב')>=0 or amud.find("ב'")>=0:
			current_daf = daf*2
		else:
			current_daf = (daf*2)-1	
		text = ""
		if amud_written_out == False:
		  for count, word in enumerate(words):
			if not (count == daf_pos or count == daf_pos+1 or count == daf_pos+2):
				text += word + " "
		else:
		  for count, word in enumerate(words):
			if not (count == daf_pos or count == daf_pos+1 or count == daf_pos+2 or count==daf_pos+3):
				text += word + " "
	elif text.find('@08ע"ב')>=0: 
		current_daf += 1
		text = text.replace('ע"ב', '')
	elif text.find('@08עמוד')>=0:
		amud_pos = -1
		words = text.split(" ")
		for count, word in enumerate(words):
			if word.find('@08עמוד')>=0:
				amud_pos = count
				break
		if words[amud_pos+1].find('ב')>=0:
			current_daf+=1
			text = ""
			for count, word in enumerate(words):
				if not (count == amud_pos or count == amud_pos+1):
					text += word + " "
		
	if not current_daf in dh_dict:
		dh_dict[current_daf] = []
	if not current_daf in comm_dict:
		comm_dict[current_daf] = []

	for tag in tags:
		text = text.replace(tag, "")
			
	if text.find("כו'")>=0 and text.find('.')>=0 and text.find("כו'")<text.find('.'):
		dh, comment = text.split("כו'",1)
		dh += "כו'"+". "
		if comment[0] == '.':
			comment = comment[1:]
	elif text.find(".")==text.rfind("."):
		comment = text
		dh = ""	
	elif text.find(".")>=0:
		dh, comment = text.split(".", 1)
		if len(dh.split(" ")) >= 20:
			comment = text
			dh = ""
		else:
			dh += ". "
			if dh.find("תוספות")>=0 or dh.find('ז"ל')>=0:
				comment = text
				dh = ""
				
  	if len(comment)>0 and comment[0] == ' ':
		comment = comment[1:]
		
	if hasTags(comment) or hasTags(dh):
		print 'tags'
		pdb.set_trace()
	return (dh, comment)


def addDHComment(dh, comment):
	if len(dh)>0:
		dh_dict[current_daf].append(dh)
		comm_dict[current_daf].append("<b>"+dh+"</b>"+comment)
	else:
		last_comment = len(comm_dict[current_daf])-1
		if last_comment == -1:
			comm_dict[current_daf].append(comment)
			dh_dict[current_daf].append("")
		else:
			comm_dict[current_daf][last_comment] += "<br>"+comment

#pattern = re.compile("@08.*? (.*?\s)?\d\d?\s?")
for count_file in range(num_files):
	if count_file < 9:
		f = open(masechet+"/"+title+str(start_title+count_file)+".txt")
	else:
		f = open(masechet+"/"+title+str(start_title+count_file)+".txt")
	for line in f:
		if len(line.replace(" ","").replace("\n",""))==0:
			continue
		line = line.replace("#36", "")
		line = line.replace("#18", "")
		line = line.replace("\n", "")
		line = line.replace("@07", "@08")
		line = line.replace("@11", "@08")
		line = line.replace("@22", "@06")
		line = line.replace("@99", "@01")
		line = line.replace("[", "")
		line = line.replace("]", "")
		#if pattern.match(line):
		#	line = line.replace(pattern.match(line).group(0),"")
		while line.find(end) >= 0:
			pos_end = line.find(end)
			current_text += line[0:pos_end]
			if len(current_text.replace(" ",""))>0:
				dh, comment = parse(current_text)
			addDHComment(dh, comment)
			line = line[pos_end+3:]
			current_text = ""
		else:
			current_text += line
		while current_text.find("@08") != current_text.rfind("@08"):
			pos_end = current_text.rfind("@08")
			parse_text = current_text[0:pos_end]
			dh, comment = parse(parse_text)
			addDHComment(dh, comment)
			current_text = current_text[pos_end:]
		prev_line = line
	if len(current_text.replace(" ",""))>0:
		print "end without tags"
		pdb.set_trace()

checkLengthsDicts(dh_dict, comm_dict)

last_daf = max(comm_dict.keys())
text_to_post = convertDictToArray(comm_dict)
send_text = {
			"versionTitle": "Vilna Ed",
			"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637",
			"language": "he",
			"text": text_to_post,
			}
post_text("Shita Mekubetzet on "+masechet, send_text, "on")

for daf in dh_dict:
	text = get_text(masechet+"."+AddressTalmud.toStr("en", daf))
	match_obj=Match(in_order=True, min_ratio=85, guess=False, range=True)
	dh_arr = dh_dict[daf]
	result = match_obj.match_list(dh_arr, text, masechet+" "+AddressTalmud.toStr("en", daf))
	for key in result:
		line_n = result[key]
		line_n = line_n.replace("0:","")
		post_link({
				"refs": [
						 masechet+"."+AddressTalmud.toStr("en", daf)+"."+line_n, 
						"Shita Mekubetzet on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(key)
					],
				"type": "commentary",
				"auto": True,
				"generated_by": "Shita on "+masechet+" linker",
			 })
