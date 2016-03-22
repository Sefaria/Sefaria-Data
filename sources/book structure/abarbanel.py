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


inv_gematria = {}
for key in gematria.keys():
	inv_gematria[gematria[key]] = key

def getGematria(txt):
	index=0
	sum=0
	while index <= len(txt)-1:
		if txt[index:index+2] in gematria:
			sum += gematria[txt[index:index+2]]
		index+=1
	return sum
	
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
		x= response.read()
		print x
		if x.find("error")>=0 and x.find("Line")>=0 and x.find("0")>=0:
			pdb.set_trace()
		
	except HTTPError, e:
		print 'Error code: ', e.code

def post_text(ref, text):
    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
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
        print 'Error code: ', e.code
        print e.read()

def isGematria(txt):
	if txt.find("ך")>=0:
		txt = txt.replace("ך", "כ") 
	if txt.find("ם")>=0:
		txt = txt.replace("ם", "מ")
	if txt.find("ף")>=0:
		txt = txt.replace("ף", "פ")
	if txt.find("ץ")>=0:
		txt = txt.replace("ץ", "צ")
	if txt.find("טו")>=0:
		txt = txt.replace("טו", "יה")
	if txt.find("טז")>=0:
		txt = txt.replace("טז", "יו")	
	if len(txt) == 2:
		letter_count = 0
		for i in range(9):
			if inv_gematria[i+1]==txt[letter_count:2+letter_count]:
				return True
			if inv_gematria[(i+1)*10]==txt[letter_count:2+letter_count]:
				return True
		for i in range(4):
			if inv_gematria[(i+1)*100]==txt[letter_count:2+letter_count]:
				return True
	elif len(txt) == 4:
	  first_letter_is = ""
	  for letter_count in range(2):
	  	letter_count *= 2
		for i in range(9):
			if inv_gematria[i+1]==txt[letter_count:2+letter_count]:
				if letter_count == 0:
					#print "single false"
					return False
				else:
					first_letter_is = "singles"
			if inv_gematria[(i+1)*10]==txt[letter_count:2+letter_count]:
				if letter_count == 0:
					first_letter_is = "tens"
				elif letter_count == 2:
					if first_letter_is != "hundred":
						#print "tens false"
						return False
		for i in range(4):
			if inv_gematria[(i+1)*100]==txt[letter_count:2+letter_count]:
				if letter_count == 0:
					first_letter_is = "hundred"
				elif letter_count == 2:
					if txt[0:2] != 'ת':
						#print "hundreds false, no taf"
						return False
	elif len(txt) == 6:
		#rules: first and second letter can't be singles
		#first letter must be hundreds
		#second letter can be hundreds or tens
		#third letter must be singles
		for letter_count in range(3):
			letter_count *= 2
			for i in range(9):
				if inv_gematria[i+1]==txt[letter_count:2+letter_count]:
					if letter_count != 4:
					#	print "3 length singles false"
						return False
					if letter_count == 0:
						first_letter_is = "singles"
				if inv_gematria[(i+1)*10]==txt[letter_count:2+letter_count]:
					if letter_count == 0:
						#print "3 length tens false, can't be first"
						return False
					elif letter_count == 2:
						if first_letter_is != "hundred":
						#	print "3 length tens false because first letter not 100s"
							return False
					elif letter_count == 4:
						#print "3 length tens false, can't be last"
						return False
			for i in range(4):
				if inv_gematria[(i+1)*100]==txt[letter_count:2+letter_count]:
					if letter_count == 0:
						first_letter_is = "hundred"
					elif letter_count == 2:
						if txt[0:2] != 'ת':
							#print "3 length hundreds false, no taf"
							return False
	else:
		print "length of gematria is off"
		print txt
		return False
	return True
	
current_perek = 1
current_pasuk = 1
current_book = "Genesis"
current_intro = ""
just_added_intro = False
comments = {}
comments["Genesis"] = {}
comments["Exodus"] = {}
comments["Leviticus"] = {}
comments["Numbers"] = {}
comments["Deuteronomy"] = {}
f = open("abarbanel.txt", "r")
for line in f:
	line = line.replace("\n", "")
	if line.find("@00")>=0:
		if line.find("שמות")>=0:
			current_book = "Exodus"
			print current_book
		elif line.find("ויקרא")>=0:
			current_book = "Leviticus"
			print current_book
		elif line.find("במדבר")>=0:
			current_book = "Numbers"
			print current_book
		elif line.find("דברים")>=0:
			current_book = "Deuteronomy"
			print current_book
	elif line.find("@88")>=0:
		line = line.replace("@88", "")
		current_intro = line
		just_added_intro = True
	elif line.find("@22")>=0:
		line = line.replace("@22", "").replace("(", "").replace(")", "")
		if isGematria(line)==False:
			pdb.set_trace()
		current_pasuk = getGematria(line)
		comments[current_book][current_perek][current_pasuk] = []
	elif line.find("@66")>=0:
		line = line.replace("@66", "")
		if isGematria(line)==False:
			pdb.set_trace()
		current_perek = getGematria(line)
		comments[current_book][current_perek] = {}
	if line.find("@11")>=0:
		line = line.replace("@11", "")
		line = line.replace("@33", "")
		if just_added_intro == True:
			comments[current_book][current_perek][current_pasuk].append(current_intro)
			just_added_intro = False
		comments[current_book][current_perek][current_pasuk].append(line)
	elif line.find("@44")>=0:
		line = line.replace("@44", "")
		line = line.replace("@55", "")
		if just_added_intro == True:
			comments[current_book][current_perek][current_pasuk].append(current_intro)
			just_added_intro = False
		comments[current_book][current_perek][current_pasuk].append(line)
		
for perek in comments:
	for pasuk in comments[perek]:
		comments[perek][pasuk] 
		send_text = {
				"versionTitle": "Torah Commentary of Yitzchak Abarbanel, Warsaw 1862",
				"versionSource": "http://www.sefaria.org",
				"language": "he",
				"text": comments,
				}
		post_text("Rashba on "+masechet+"."+AddressTalmud.toStr("en", daf), send_text)
		post_link({
				"refs": [
						 which_book+"."+str(perek)+"."+str(pasuk),
						"Abarbanel on Torah."+str(perek)+"."+str(pasuk)
					],
				"type": "commentary",
				"auto": True,
				"generated_by": "Abarbanel linker",
			 })