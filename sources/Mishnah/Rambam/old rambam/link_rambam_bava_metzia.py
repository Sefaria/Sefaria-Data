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
import re
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)

from sefaria.model import *
from match import Match

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

title_book = "Mishnah Yevamot"
title_comm = "Rambam on Mishnah Yevamot" 

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

def get_index(ref):
 	ref = ref.replace(" ", "_")
 	url = 'http://www.sefaria.org/api/texts/'+ref
 	req = urllib2.Request(url)
 	try:
 		response = urllib2.urlopen(req)
 		data = json.load(response)
 		return data
 	except: 
 		print 'Error'
        
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
		if list[0] == 0:
			log.append(hyperlink+"."+str(siman)+"."+str(count)+"\nNot Matched\n\n")
		elif len(list) > 1:
			guess_str = hyperlink+"."+str(siman)+"."+str(count)+"\nGuessed line "+str(list[0])+", but other options include line(s) "
			for guess in list:
				if guess != list[0]:
					guess_str += str(guess)+","
			guess_str = guess_str[0:-1]
			log.append(guess_str+"\n\n")
		count+=1
	return log

comm = {}
book = {}
total = 0
non_match = 0
guess = 0
matched = 0
log = []

f=open('yevamot.txt', 'r')
f.readline() #just says rambam on shabbos
perek_num = 0
dh_dict = {}
curr_dh_count = 0 
curr_dh = ""
comm = {}

for line in f:
	line = line.replace("\n", "")
	line = line.replace(":", "")
	if line.find("@00") >= 0:
		perek_num+=1
	elif line.find("@11") >= 0:
		curr_dh_count += 1
		line = line.replace("@11", "")
		daf = re.compile('@22\(.*?\)')
		match = re.search(daf, line)
		if match:
			line = line.replace(match.group(0), "")
		if perek_num in dh_dict:
			dh_dict[perek_num].append(line)
		else:
			dh_dict[perek_num] = []
			dh_dict[perek_num].append(line)
		curr_dh = line	
	elif line.find("@33") >= 0:
		line = line.replace("@33", "")
		for i in range(curr_dh_count):
			if perek_num in comm:
				comm[perek_num].append(line)
			else:
				comm[perek_num] = []
				comm[perek_num].append(line)
		curr_dh_count = 0
f.close()

#at end of this, for each comm[perek is a list of rambam's comments and for each perek is a list of the dhs
#for each perek, figure out how many mishnayot are in that perek, grab them all and send them to match with list of dhs for that perek

for j in range(perek_num):
	perek = {}
	perek[j+1] = get_text(title_book+"."+str(j+1))
	if len(dh_dict[j+1]) > 0: 
		match_obj=Match(in_order=True, min_ratio=70, guess=False)
		result = match_obj.match_list(dh_dict[j+1], perek[j+1], j+1)
		matched += getMatched(result)
		total += getTotal(result)
		guess += getGuesses(result)
		non_match += getNotMatched(result)
		log_info = getLog("http://dev.sefaria.org/"+title_comm, j+1, result)
		if log_info != []:
			log.append(log_info)
		result_dict = {}
		for key in result:
			dh = """<b>"""+dh_dict[j+1][key-1]+"""</b>. """
			mishnah_n = result[key][0]
			if mishnah_n in result_dict:
				result_dict[mishnah_n] += 1
			else:
				result_dict[mishnah_n] = 1
			if mishnah_n > 0:
				text = {
				"versionTitle": title_comm,
				"versionSource": "",
				"language": "he",
				"text": dh+comm[j+1][key-1],
				}
				post_text(title_comm+"."+str(j+1)+"."+str(mishnah_n)+"."+str(result_dict[mishnah_n]), text)		

title_comm = title_comm.replace(" ", "_")
if os.path.exists("log_"+title_comm+".txt") == True:
	os.remove("log_"+title_comm+".txt")	
log_file = open("log_"+title_comm+".txt", "w")
for arr in log:
	for line in arr:
		log_file.write(str(line))
	
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