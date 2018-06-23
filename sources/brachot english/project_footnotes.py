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
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	



def removeFootnote(str):
	len_str = len(str)
	new_str = ""
	how_many_words = len(str.split(" "))
	return " ".join(str.split(" ")[1:how_many_words])
	
def convertNumber(str):
	str = str.replace("[","").replace("]","")
	new_str = ""
	for i in range(len(str)):
		if str[i].isdigit():
			new_str += str[i]
	return int(new_str)
	
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

def get_text(ref, site):
 	ref = ref.replace(" ", "_")
 	url = site+'/api/texts/'+ref
 	req = urllib2.Request(url)
 	try:
 		response = urllib2.urlopen(req)
 		data = json.load(response)
 		return data
 	except: 
 		return 'Error'

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

footnotes = []
filenames = ["BT_Chapter I Footnotes.txt", "BT_Chapter II Footnotes.txt", "BT_Chapter III Footnotes.txt", "BT_Chapter IV Footnotes.txt",
"BT_Chapter V Footnotes.txt", "BT_Chapter VI Footnotes.txt", "BT_Chapter VII Footnotes.txt", "BT_Chapter VIII Footnotes.txt",
"BT_Chapter IX Footnotes.txt"]
is_a_num = re.compile('\d+')
log_file = open('log_pages_hebrew.txt', 'a')
prev_footnote = 0
flag = 0
count=0
loc_page_breaks = {}
loc_hebrew_chars = {}
for filename in filenames:
	file = open(filename)
	for line in file:
		line = line.replace("\n", "")
		line = line.replace("\r", "")
		first_word = line.split(" ")[0]
		if first_word == "Page:" or first_word == "Page":	
			page_num = line.split(" ")[1]
			if page_num == ':':
				page_num = line.split(" ")[2]
			flag = 0
			loc_page_breaks[count] = True
		if line.find("***") >= 0:
			loc_hebrew_chars[count] = page_num
		match = is_a_num.match(first_word)
		if match:
			curr_footnote = int(match.group(0))
			if flag == 1 and curr_footnote - 1 != prev_footnote:
				pdb.set_trace()
			if curr_footnote - 1 != prev_footnote:
				flag = 1
			else:
				flag = 0
			footnotes.append(line)
			count+=1
			prev_footnote = curr_footnote
footnotes_per_daf = {}
footnote=2865
again=0
title_comm = "Abraham Cohen Footnotes to the English Translation of Masechet Berakhot"
skip_line = 86
skip_daf = 122
footnotes_missing = open('log_missing.txt', 'w')
recently_found_arr = []
just_found_this_one = False
for i in range(124):
	j = i + 3
	if j < skip_daf:
		continue
	print SEFARIA_SERVER
	text = get_text("Berakhot."+AddressTalmud.toStr("en", j), 'http://dev.sefaria.org')['text']
	posted_text = get_text(title_comm+"."+AddressTalmud.toStr("en", j), SEFARIA_SERVER)['text']
	print "*******************"
	print len(posted_text)
	footnotes_per_daf[j] = len(posted_text)
	for line_n, line in enumerate(text):
		if j==skip_daf and line_n < skip_line:
			continue
		p = re.compile('.*\[\d+\].*')
		words = line.split(" ")
		for word in words:
			match = p.match(word)
			if match:
				comment = footnotes[footnote] 
				number = comment.split(" ")[0]
				if footnote in loc_page_breaks:  
					recently_found_arr = []
				for recently_found in recently_found_arr:
					if recently_found in word:
						just_found_this_one = True
				if just_found_this_one:
					just_found_this_one = False
					print "JUST FOUND THIS ONE"
					print word
					continue
				if number not in word:
					print "page: "+AddressTalmud.toStr("en", j)+"\nexpecting "+comment+" but found "+line.encode('utf-8')+"\n"
					pdb.set_trace()
				else:
					print AddressTalmud.toStr("en", j)
					print line
					print comment
				recently_found_arr.append("["+str(number)+"]")
				comment = removeFootnote(comment)
				if footnote in loc_hebrew_chars:
					page_num = loc_hebrew_chars[footnote]
					log_file.write('Found Hebrew characters on page '+str(page_num)+'\n')
					log_file.write("http://www.sefaria.org/Abraham_Cohen_Footnotes_to_the_English_Translation_of_Masechet_Berakhot."+AddressTalmud.toStr("en", j)+'\n\n')
				footnote+=1
				footnotes_per_daf[j]+=1
				send_text = {
				"versionTitle": "Tractate Berakot by A. Cohen, Cambridge University Press, 1921",
				"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002182132",
				"language": "en",
				"text": comment,
				"license": "Public Domain",
				"status": "locked"
				}
				prev_num = number
				post_text(title_comm+"."+AddressTalmud.toStr("en", j)+"."+str(footnotes_per_daf[j]), send_text)
				post_link({
					"refs": [
							"Berakhot"+"."+AddressTalmud.toStr("en", j)+"."+str(line_n+1), 
							title_comm+"."+AddressTalmud.toStr("en", j)+"."+str(footnotes_per_daf[j])
						],
					"type": "commentary",
					"auto": True,
					"generated_by": title_comm+"linker",
				 })
				 
				 
footnotes_missing.close()
log_file.close()

print again