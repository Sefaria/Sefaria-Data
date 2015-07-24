# -*- coding: utf8 -*-

# -*- coding: utf-8 -*-
import json
import os
import sys
import pprint
import pdb
import urllib
import urllib2
from urllib2 import URLError, HTTPError
from match import Match
import re
p = os.path.dirname(os.path.abspath(__file__))
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

title_book = "Berakhot"
title_comm = "Rashi on Berakhot" 

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
	url = 'http://dev.sefaria.org/api/links/'
	infoJSON = json.dumps(info)
	values = {
		'json': infoJSON, 
		'apikey': 'F4J2j3RF6fHWHLtmAtOTeZHE3MOIcsgvcgtYSwMzHtM'
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

def getLog(hyperlink, siman, result):
	log = []
	count = 1
	for key in result:
		list = result[key]
		if len(list) == 1 and list[0] == 0:
			log.append(hyperlink+"."+str(siman)+"."+str(count)+"\nNot Matched\n\n")
		elif len(list) > 1:
			guess_str = hyperlink+"."+str(siman)+"."+str(count)+"\nGuessed line "+str(list[0])+", but other options include line(s) "
			for guess in list:
				if guess != list[0]:
					guess_str += str(guess)+","
			guess_str = guess_str[0:-1]
			log.append(guess_str)
		count+=1
	return log

comm = {}
book = {}
total = 0
non_match = 0
guess = 0
matched = 0
log = []
dh_list = []
rashi_comments = []
prev_line = 0
for j in range(24): #actually 124
	i = j+100
	count = 0
	dh_list=[]
	rashi_comments = []
	he_daf = u"ברכות_"
	he_daf += AddressTalmud.toStr("he", i+3)
	he_daf = he_daf.replace(u"\u05f4", u"")
	he_daf = he_daf.replace(u"׳", u"")
	he_daf = he_daf.replace(" ", "_")
	he_daf = he_daf + ".txt"
	f = open("Rashi/"+he_daf, 'r')
	for line in f:
		line = line.replace("\n", "")
		something = line.replace(" ", "")
		if len(something) > 0:
			if count % 2 == 0:
				dh_list.append(line)
			else:
				rashi_comments.append(line)
			count+=1
	f.close()		
	book[str(i+3)] = get_text(title_book+"."+AddressTalmud.toStr("en", i+3))
	lines = len(book[str(i+3)])
	if len(dh_list) > 0: 
		match_obj=Match(in_order=True, min_ratio=70, guess=True)
		result=match_obj.match_list(dh_list, book[str(i+3)], (i+3))
		matched += getMatched(result)
		total += getTotal(result)
		guess += getGuesses(result)
		non_match += getNotMatched(result)
		#log_info = getLog("http://dev.sefaria.org/Beit_Shmuel", i+3, result)
		#if log_info != []:
	#		log.append(log_info)
		result_dict = {}
		for key in result:
			line_n = result[key][0]
			if line_n in result_dict:
				result_dict[line_n] += 1
			else:
				result_dict[line_n] = 1
			if line_n > 0:
				text = {
				"versionTitle": "SMK on Berakhot",
				"versionSource": "nothing",
				"language": "he",
				"text": rashi_comments[key-1],
				}
				post_text("SMK on Berakhot."+AddressTalmud.toStr("en", i+3)+"."+str(line_n)+"."+str(result_dict[line_n]), text)
				#createLinks(result, i+3)
		

if os.path.exists("log_"+title_comm+".txt") == True:
	os.remove("log_"+title_comm+".txt")	
#log_file = open("log_"+title_comm+".txt", "w")
#for line in log:
#	log_file.write(str(line))
	
#log_file.close()

print str(total) + " = Total"
print str(non_match) + " = Non-matches"
print str(matched) + " = Matches"
print str(guess) + " = Guesses"
#match first goes through each line comparing it with dh
#adding each match by line number to list_of_found_links 
#for each line that matches dh, increment 'found' counter
#add condition to match ifs:
#check if this is an acronym with a ", 
#if it is, for loop through acronyms checking if acronym is inside 'dh', 
#new_dh = dh.replace(acronym, expansion)
#if it is, check if new_dh in line, and check if fuzz.partial_ratio(line, new_dh)
#after loop, check if found > 1, ==1, ==0
#if found > 1: set more_than_one to true and all lines to dict
#if found == 1: set more_than_one to false, consider it a match
#if found == 0:
#try again with lower ratio
#error_log=open('error_log', 'w')
	
'''double dict function:
dh_dict is dictionary where keys are siman numbers and value is an in order list of dh's in that siman
therefore:
match should create data structure, found_dict, where each siman number maps to dictionary where
keys are tuples of dh_position (position in dh_dict[siman_num] array)
and matched (found>=1) dh's and where the value is a list of line numbers

confirmed_dict  = {}
for each tuple of (dh_pos, dh) in found_dict whose list's length == 1
	simply set confirmed_dict[siman_num][(dh_pos, dh)] = line_num
for each tuple of (dh_pos, dh) in found_dict whose list's length is > 1 where siman_num is current siman number:
	find maximum and minimum line numbers for this dh 
		do this by setting i to dh_pos
		starting at i-1, counting down to 1, we look for the first dh = dh_dict[siman_num][i]
		such that confirmed_dict[siman_num][(i, dh)]'s length is 1 or we just use line 1
		we then set confirmed_dict[siman_num][(i, dh)] to line_n
		 (???? what if previous dh is 0?  ignore it)
		starting at i+1, counting until highest line, we look for the first dh_dict[siman_num][i]
		such that it's found == 1, or we just use highest line
	
	once we find max and min, we go through each dh, only adding them to our final_list
	if the line they occur on is <=max and >=min
	
	if there are still multiples left over, pick the first or middle one
		
'''