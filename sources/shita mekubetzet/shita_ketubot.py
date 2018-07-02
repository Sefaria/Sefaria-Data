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


title = "P"
start_title = 1
masechet = "Ketubot"
end = "@01"
num_files = 191
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
	amud_written_out=False
	tags = ["@07", "@06", "@05", "@04", "@08", "@24", "@14", "@33", "@09", "@02"]
	text = text.replace("@05@04", "@06")
	text = text.replace("@19", "@06")
	if text.find("08") != text.rfind("08"):
		print "TWO 08s"
		pdb.set_trace()
	words = text.split(" ")
	if words[0].find("דף")>=0 or words[1].find("דף")>=0:
		if words[0].find("דף")>=0:
			daf_pos = 0
		else:
			daf_pos = 1 
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
	elif words[0].find('ע"ב')>=0 or words[1].find('ע"ב')>=0:
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
				
  	if comment[0] == ' ':
		comment = comment[1:]
	if hasTags(comment) or hasTags(dh):
		print 'tags'
		pdb.set_trace()
	return (dh, comment)

comment_wout_dh = False

def addDHComment(dh, comment):
	if len(dh)>0:
		dh_dict[current_daf].append(dh)
		comm_dict[current_daf].append("<b>"+dh+"</b>"+comment)
	else:
		last_comment = len(comm_dict[current_daf])-1
		if last_comment == -1:
			comm_dict[current_daf].append(comment)
			dh_dict[current_daf].append("")
			comment_wout_dh = True
		else:
			comm_dict[current_daf][last_comment] += "<br>"+comment

p = re.compile("@08בבא בתרא(\d\d)?")
t_words = open('3words.txt', 'w')
for count_file in range(num_files):
	if count_file == 69:
		continue
	if count_file < 9:
		f = open(masechet+"/"+title+"00"+str(start_title+count_file)+".txt")
	elif count_file < 99:
		f = open(masechet+"/"+title+"0"+str(start_title+count_file)+".txt")
	else:
		f = open(masechet+"/"+title+str(start_title+count_file)+".txt")
	for line in f:
		if len(line.replace(" ","").replace("\n",""))==0:
			continue
		line = line.replace("@03", "@01")
		line = line.replace("@71", "@01")
		line = line.replace("#36", "")
		line = line.replace("#18", "")
		line = line.replace("\n", "")
		line = line.replace("@61", "@08")
		line = line.replace("@07", "@08")
		if p.match(line):
			line = line.replace(p.match(line).group(0),"")
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
		begin_tags = ["@08", "@02"]
		for tag in begin_tags:
			if current_text.find(tag) != current_text.rfind(tag):
				pos_end = current_text.rfind(tag)
				parse_text = current_text[0:pos_end]
				dh, comment = parse(parse_text)
				addDHComment(dh, comment)
				current_text = current_text[pos_end:]
		prev_line = line
	if len(current_text.replace(" ",""))>0:
		print "end without tags"
		pdb.set_trace()

for daf in dh_dict:
	if len(dh_dict[daf]) != len(comm_dict[daf]):
		print "lengths off"
		pdb.set_trace()

text_to_post = convertDictToArray(comm_dict)
send_text = {
			"versionTitle": "Shita Mekubetzet on "+masechet,
			"versionSource": "http://www.sefaria.org",
			"language": "he",
			"text": text_to_post,
			}
#post_text("Shita Mekubetzet on "+masechet, send_text, "on")

links_to_post = []
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
