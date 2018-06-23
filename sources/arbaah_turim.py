# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import sys
import re
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *


SCT = {}
Warsaw_1861 = {}
OnYourWay = {}

OnYourWay['text'] = get_text_plus("Arba'ah_Turim/he/OnYourWay", 'draft')['he']
OnYourWay['length'] = 1
OnYourWay['versionTitle'] = "OnYourWay"
OnYourWay['versionSource'] = "mobile.tora.ws"
OnYourWay['language'] = "he"

SCT['text'] = get_text_plus("Arba'ah_Turim/en/Sefaria_Community_Translation", 'draft')['text']
SCT['length'] = 2
SCT['versionTitle'] = "Sefaria Community Translation"
SCT['versionSource'] = "www.sefaria.org"
SCT['language'] = "en"

Warsaw_1861['text'] = get_text_plus("Arba'ah_Turim/he/Warsaw_1861", 'draft')['he']
Warsaw_1861['length'] = 4
Warsaw_1861['versionTitle'] = "Warsaw 1861"
Warsaw_1861["language"] = "he"
Warsaw_1861["versionSource"] = "commons.wikimedia.org"

helekim = ["Orach Chaim", "Yoreh Deah", "Even HaEzer", "Choshen Mishpat"]
Versions = [SCT, OnYourWay, Warsaw_1861]

for count, helek in enumerate(helekim):
	if helek != "Choshen Mishpat":
		continue
	for i in range(len(Versions)):
		print i
		if Versions[i]['length'] > count:
			print Versions[i]["versionTitle"]
			print helek
			send_text = {
				"text": Versions[i]['text'][count],
				"language": Versions[i]["language"],
				"versionTitle": Versions[i]["versionTitle"],
				"versionSource": Versions[i]["versionSource"]
			}
			post_text("Tur,_"+helek.replace(" ", "_"), send_text)



