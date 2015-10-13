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
	new_str = ""
	for i in range(len(str)):
		if str[i].isdigit() and str[i-1]=='[':
			new_str += str[i]
	return int(new_str)
	
def post_text(ref, text):
    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    url = SEFARIA_SERVER+'api/texts/'+ref
    values = {'json': textJSON, 'apikey': API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except HTTPError, e:
        print 'Error code: ', e.code
        print e.read()
def get_text(ref):
 	ref = ref.replace(" ", "_")
 	url = 'http://www.sefaria.org/api/texts/'+ref
 	req = urllib2.Request(url)
 	try:
 		response = urllib2.urlopen(req)
 		data = json.load(response)
 		return data
 	except: 
 		return 'Error'
 
footnotes = []
filenames = ["BT_Chapter I Footnotes.txt", "BT_Chapter II Footnotes.txt", "BT_Chapter III Footnotes.txt", "BT_Chapter IV Footnotes.txt",
"BT_Chapter V Footnotes.txt", "BT_Chapter VI Footnotes.txt", "BT_Chapter VII Footnotes.txt", "BT_Chapter VIII Footnotes.txt",
"BT_Chapter IX Footnotes.txt"]
is_a_num = re.compile('\d+')
log_file = open('log_pages_hebrew.txt', 'w')
prev_footnote = 0
flag = 0
for filename in filenames:
	file = open(filename)
	for line in file:
		line = line.replace("\n", "")
		line = line.replace("\r", "")
		first_word = line.split(" ")[0]
		if first_word == "Page:" or first_word == "Page":	
			page_num = line.split(" ")[1]
			flag = 0
		if line.find("***") >= 0:
			log_file.write('Found Hebrew characters on page '+str(page_num)+'\n')
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
			prev_footnote = curr_footnote
footnotes_per_line = {}
footnote=0
log_file.close()
again=0
title_comm = "Footnotes on Berakhot"
footnotes_missing = open('log_missing.txt', 'w')
for i in range(124):
	j = i + 3
	print j
	text = get_text("Berakhot."+AddressTalmud.toStr("en", j))['text']
	for line_n, line in enumerate(text):
		p = re.compile('.*\[\d+\].*')
		words = line.split(" ")
		for word in words:
			match = p.match(word)
			if match:
				number = convertNumber(match.group(0))
				comment = footnotes[footnote] 
				if int(comment.split(" ")[0]) < number:
					print "low"
					footnote+=1
					footnotes_missing.write("page: "+AddressTalmud.toStr("en", j)+"\nexpecting "+comment.split(" ")[0]+" but found "+line.encode('utf-8')+"\n") 
				elif int(comment.split(" ")[0]) > number:
					print "high"
					footnote-=1
					footnotes_missing.write("page: "+AddressTalmud.toStr("en", j)+"\nexpecting "+comment.split(" ")[0]+" but found "+line.encode('utf-8')+"\n") 					
				comment = removeFootnote(comment)
				footnote+=1
				if (line_n+1, j) in footnotes_per_line:
					footnotes_per_line[(line_n+1, j)]+=1
				else:
					footnotes_per_line[(line_n+1, j)]=1
				send_text = {
				"versionTitle": "Tractate Berakot by A. Cohen, Cambridge University Press, 1921",
				"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002182132",
				"language": "en",
				"text": comment,
				}
				#post_text(title_comm+"."+AddressTalmud.toStr("en", j)+"."+str(line_n+1)+"."+str(footnotes_per_line[(line_n+1,j)]), send_text)
footnotes_missing.close()
print again