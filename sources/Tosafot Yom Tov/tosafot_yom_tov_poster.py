
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



def post_text(ref, text):
    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    url = SEFARIA_SERVER+'api/texts/'+ref
    values = {'json': textJSON, 'apikey': API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        x = response.read()
        if x.find("0")>=0:
        	pdb.set_trace()
    except HTTPError, e:
        print 'Error code: ', e.code
        print e.read()

def post_link(info):
	url = SEFARIA_SERVER+"api/links/"
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

def createLinks(perek, mishnah, comment):
	#first check that this mishnah exists
	len_perek = len(get_index(title_book+"."+str(perek))['text'])
	if mishnah > len_perek:
		print "mishnah doesn't exist"
		pdb.set_trace()
	post_link({
		"refs": [
				title_book+"."+str(perek)+"."+str(mishnah), 
				title_comm+"."+str(perek)+"."+str(mishnah)+"."+str(comment)
			],
		"type": "commentary",
		"auto": True,
		"generated_by": title_comm+title_book+"linker",
	 })
	

def gematriaFromSiman(txt):
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
 		return 'Error'
        
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
		mishnah_n = result[key]
		if mishnah_n[0] == 0:
			append_str = "did not find dh:\n"+str(dh_dict[siman][key-1])+"\n in "+title_book+", Perek "+str(siman)+":"
			append_str += "\nwww.sefaria.org/"+title_book.replace(" ", "_")+"."+str(siman)
			append_str += "\ntext:<b>"+str(dh_dict[siman][key-1])+".</b> "+str(comm[siman][key-1])+"\n\n"
			log.append(append_str)
		elif len(mishnah_n) > 1:
			bestGuess = mishnah_n[0]
			guess_str = "looked for dh:\n"+str(dh_dict[siman][key-1])+"\n in "+title_book+", Perek "+str(siman)
			guess_str += " and guessed the dh matches to mishnah "+str(bestGuess)+":"
			title_c = title_comm.replace(" ", "_")
			guess_str += "\nwww.sefaria.org/"+title_c+"."+str(siman)+"."+str(bestGuess)
			guess_str += "\nbut other options include:\n"
			for guess in mishnah_n:
				if guess != mishnah_n[0]:
					title = title_book.replace(" ", "_")
					guess_str += "mishnah " +str(guess)+": www.sefaria.org/"+title+"."+str(siman)+"."+str(guess)+" ,\n"
			guess_str = guess_str[0:-1]
			log.append(guess_str+"\n\n")
	return log


def separateDH_Comm(line):
	line = line.replace("@11", "")
	line = line.replace("@22", "")
	line = line.replace("@33", "")
	line = line.replace("@44", "")
	line = line.replace("@55", "")
	line = line.replace("@88", "")
	line = line.replace("@66", "")
	line = line.replace("@77", "")
	line = line.replace("&", "")
	line = line.replace("*", "")
	line = line.replace("#", "")
	
	dh = line.split(".")[0]+". "
	comm = ""
	len_words = len(line.split("."))-1
	for count, word in enumerate(line.split(".")):
		if count > 0 and count < len_words:
			comm += word + ". "
		if count == len_words:
			comm += word
	return (comm, dh)

comm = {}
book = {}
total = 0
non_match = 0
guess = 0
matched = 0
log = []
title = ""
if len(sys.argv) == 2:
	title = sys.argv[1]
	title_comm = "Tosafot Yom Tov on Mishnah "+title.capitalize()
	title_book = "Mishnah "+title.capitalize()
elif len(sys.argv) == 3:
	title = sys.argv[1]+"_"+sys.argv[2]
	title_comm = "Tosafot Yom Tov on Mishnah "+sys.argv[1].capitalize()+" "+sys.argv[2].capitalize()
	title_book = "Mishnah "+sys.argv[1].capitalize()+" "+sys.argv[2].capitalize()
f=open(title+".txt", 'r')
perek_num = 0
mishnah_num = 0
dh_comm_dict = {}
comm_dict = {}
for line in f:
	line = line.replace('\n', '')
	if line.find("@00") >= 0: #NEW PEREK
		perek = line.replace(" ", "")
		perek = perek.replace("@00פרק", "")
		perek = perek.replace('@00פ"', "")
		perek = perek.replace('@00פ', "")
		perek = perek.replace("\n", "")
		perek_num = gematriaFromSiman(perek)
		dh_comm_dict[perek_num] = {}
	elif line.find("@22") >= 0: #NEW MISHNAH
		mishnah = line.split(" ")[0]
		mishnah = mishnah.replace("@22", "")
		mishnah = mishnah.replace("[*", "")
		mishnah = mishnah.replace(" ", "")
		mishnah_num = gematriaFromSiman(mishnah)
		if len(line.split(" "))>2:
			new_line = ""
			for count, word in enumerate(line.split(" ")):
				if count > 0:
					new_line += word + " "
			comm, dh = separateDH_Comm(new_line)
			if not mishnah_num in dh_comm_dict[perek_num]:
				dh_comm_dict[perek_num][mishnah_num] = []
			dh_comm_dict[perek_num][mishnah_num].append("<b>"+dh+"</b>"+comm)
	elif line.find("@11") >= 0:	#DH and commentary
		comm, dh = separateDH_Comm(line)
		if not mishnah_num in dh_comm_dict[perek_num]:
			dh_comm_dict[perek_num][mishnah_num] = []
		dh_comm_dict[perek_num][mishnah_num].append("<b>"+dh+"</b>"+comm)
f.close()
perek = {}
#for each perek, for each mishnah, post dh_dict[p][m] + comm[p][m] to Tosefot Yom Tov, Mishnah ***.p.m
#then create link between Tosefot Yom Tov.p.m.comment and Mishnah ***.p.m.comment
for each_perek in dh_comm_dict:
	for each_mishnah in dh_comm_dict[each_perek]:
		text = {
		"versionTitle": "Mishnah with 73 commentaries",
		"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002036659",
		"language": "he",
		"text": dh_comm_dict[each_perek][each_mishnah],
		}
		post_text(title_comm+"."+str(each_perek)+"."+str(each_mishnah), text)
		for each_comment in range(len(dh_comm_dict[each_perek][each_mishnah])):
			createLinks(each_perek, each_mishnah, each_comment+1)