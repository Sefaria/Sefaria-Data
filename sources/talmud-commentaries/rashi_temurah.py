# -*- coding: utf-8 -*-
import json
import os
import sys
import pprint
import pdb
import urllib
import urllib2
from urllib2 import URLError, HTTPError
sys.path.insert(0, '../Match/')
from match import Match
import re
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)

from sefaria.model import *
from sefaria.model.schema import AddressTalmud	

found_dict = {}
confirmed_dict = {}
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

def createLinks(result, siman_num):
	for key in result:
		if str(key).isdigit() == True:
			line_in_MA = key
			line_in_SA = result[key][0]
			if line_in_SA > 0:
				post_link({
					"refs": [
							title_book+"."+str(siman_num)+"."+str(line_in_SA), 
							title_comm+"."+str(siman_num)+"."+str(line_in_MA)
						],
					"type": "commentary",
					"auto": True,
					"generated_by": title_comm+title_book+"linker",
				 })
        

def gematriaFromSiman(line):
	txt = line.split(" ")[1]
	index=0
	sum=0
	while index <= len(txt)-1:
		if txt[index:index+2] in gematria:
			sum += gematria[txt[index:index+2]]
		index+=1
	return sum


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

def getMatched(result):
	count = 0
	for key in result:
		if len(result[key])==1 and result[key][0] > 0:
			count+=1
	return count

def getTotal(result):
	count = 0
	for list in result:
		count+=1
	return count

def getGuesses(result):
	count = 0
	for key in result:
		if len(result[key]) > 1:
			count+=1
	return count
	
def getNotMatched(result):
	count = 0
	for key in result:
		if len(result[key]) == 1 and result[key][0] == 0:
			count+=1
	return count

def getLog(siman, result, dh_dict, comm):
	log = []
	for key in result:
		line_n = result[key]
		if line_n[0] == 0:
			append_str = "did not find dh:\n"+str(dh_dict[siman][key-1])+"\n in "+title_book+", Daf "+AddressTalmud.toStr("en", siman)+":"
			append_str += "\nwww.sefaria.org/"+title_book.replace(" ", "_")+"."+AddressTalmud.toStr("en", siman)
			append_str += "\ntext:<b>"+str(dh_dict[siman][key-1])+".</b> "+str(comm[siman][key-1])+"\n\n"
			log.append(append_str)
		elif len(line_n) > 1:
			bestGuess = line_n[0]
			guess_str = "looked for dh:\n"+str(dh_dict[siman][key-1])+"\n in "+title_book+", Daf "+AddressTalmud.toStr("en", siman)
			guess_str += " and guessed the dh matches to line "+str(bestGuess)+":"
			title_c = title_comm.replace(" ", "_")
			guess_str += "\nwww.sefaria.org/"+title_c+"."+AddressTalmud.toStr("en", siman)+"."+str(bestGuess)
			guess_str += "\nbut other options include:\n"
			for guess in line_n:
				if guess != line_n[0]:
					title = title_book.replace(" ", "_")
					guess_str += "line " +str(guess)+": www.sefaria.org/"+title+"."+AddressTalmud.toStr("en", siman)+"."+str(guess)+" ,\n"
			guess_str = guess_str[0:-1]
			log.append(guess_str+"\n\n")
	return log

comm = {}
book = {}
total = 0
non_match = 0
guess = 0
matched = 0
log = []
dh_dict = {}
rashi_comments = {}
prev_line = 0

title_book = "Temurah"
title_comm = "Rashi on Temurah" 

for i in range(65): 
	count = 0
	rashi_comments[i+3] = []
	dh_dict[i+3] = []
	he_daf = u"תמורה_"
	he_daf += AddressTalmud.toStr("he", i+3)
	he_daf = he_daf.replace(u"\u05f4", u"")
	he_daf = he_daf.replace(u"׳", u"")
	he_daf = he_daf.replace(" ", "_")
	he_daf = he_daf + ".txt"
	f = open("../Noah-Santacruz-rashiPosting/Rashi/"+he_daf, 'r')
	for line in f:
		line = line.replace("\n", "")
		something = line.replace(" ", "")
		if len(something) > 0:
			if count % 2 == 0:
				dh_dict[i+3].append(line)
			else:
				rashi_comments[i+3].append(line)
			count+=1
	f.close()	
comments = 0
for i in range(65):
	book[str(i+3)] = get_text(title_book+"."+AddressTalmud.toStr("en", i+3))
	lines = len(book[str(i+3)])
	if len(dh_dict[i+3]) > 0: 
		match_obj=Match(in_order=True, min_ratio=70, guess=False)
		result=match_obj.match_list(dh_dict[i+3], book[str(i+3)], "Temurah "+AddressTalmud.toStr("en", i+3))
		matched += getMatched(result)
		total += getTotal(result)
		guess += getGuesses(result)
		non_match += getNotMatched(result)
		log_info = getLog(i+3, result, dh_dict, rashi_comments)
		if log_info != []:
			log.append(log_info)
		result_dict = {}
		for key in result:
			line_n = result[key][0]
			if line_n in result_dict:
				result_dict[line_n] += 1
			else:
				result_dict[line_n] = 1
			if line_n > 0:
				text = {
				"versionTitle": "WikiSource_new",
				"versionSource": "https://he.wikisource.org/wiki/תלמוד_בבלי",
				"language": "he",
				"text": rashi_comments[i+3][key-1],
				}
				comments +=1
				post_text(title_comm+"."+AddressTalmud.toStr("en", i+3)+"."+str(line_n)+"."+str(result_dict[line_n]), text)
				#createLinks(result, i+3)
		
if os.path.exists("log_"+title_comm+".txt") == True:
	os.remove("log_"+title_comm+".txt")	
log_file = open("log_"+title_comm+".txt", "w")
for lines in log:
	for line in lines:
		log_file.write(str(line))
	
log_file.close()
print comments
print str(total) + " = Total"
print str(non_match) + " = Non-matches"
print str(matched) + " = Matches"
print str(guess) + " = Guesses"