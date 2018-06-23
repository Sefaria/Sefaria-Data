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
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	
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

dh_dict = {}
magen_avraham = {}
shulchan_aruch = {}
title= "Chelkat Mechokek"
dh_file = open('chelkat_dh', 'r')
print SEFARIA_SERVER
curr_siman = 0
for line in dh_file:
	no_spaces = line.replace(" ", "")
	no_return = no_spaces.replace("\n", "") #empty if blank line
	if line.find('סימן') >= 0:
		curr_siman = gematriaFromSiman(line)
		dh_dict[curr_siman] = []
	elif len(no_return) > 0:
		line = line.replace("\n", "")
		dh_dict[curr_siman].append(line)
dh_file.close()
for i in range(144):
	magen_avraham[str(i+1)] = get_text(title+" "+str(i+1))
	shulchan_aruch[str(i+1)] = get_text("Shulchan Arukh, Even HaEzer "+str(i+1))
 	if len(magen_avraham[str(i+1)]) > 0: #Magen doesn't skip this siman
		dh_list = dh_dict[i+1]
		match_obj=Match(in_order=True, min_ratio=70, guess=False)
		result=match_obj.match_list(dh_list, shulchan_aruch[str(i+1)])
		for key in result:
			line_in_SA = result[key][0]
			if line_in_SA > 0:
				post_link({
					"refs": [
							"Shulchan_Arukh,_Even_HaEzer."+str(i+1)+"."+str(line_in_SA), 
							"Chelkat_Mechokek."+str(i+1)+"."+str(key)
						],
					"type": "commentary",
					"auto": True,
					"generated_by": "chelkat_shulchan_aruch_linker",
				 })
       		 