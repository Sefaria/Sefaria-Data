# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys
import re
import glob
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *


sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud



def getText(file):
	text = ""
	for line in open(file+".txt"):
		if line.find('@') == line.rfind('@') and line.find('@13')>=0:
			line = line.replace('\n', '')
		text += line.replace('@00', '').replace('@44', '<b>').replace('@55', '</b>')
	return text


def getAmudimAndLinks(text):
	text = text.split("@20")
	for amud_count in range(len(text)):
		text[amud_count] = text[amud_count].split('\n')
		links[amud_count] = []
		for comment in text[amud_count]:
			matches = re.findall(u'\(@13דף [\u05D0-\u05EA]+ ע"[א|ב]\)', comment)
			dappim_to_link_to = deriveDappim(matches)
			links[amud_count].append(dappim_to_link_to)
			for match in matches:
				comment = comment.replace(match, "")
	return text, links


def deriveDappim(matches):
	actual_values = []
	for match in matches:
		match_arr = match.split(" ")
		daf = match_arr[1]
		amud = match_arr[2].replace(u'ע', '')
		value = 2 * getGematria(daf) - (amud % 2)
		actual_values.append(value)
	return actual_values



def postRif(amudim, links):
	send_text = {
		"text": amudim,
		"versionTitle": "Vilna Edition",
		"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
		"language": "he"
	}
	post_text("Rif_Megillah", send_text)


if __name__ == "__main__":
	files = ["Megillah", "Nedarim"]
	for file in files:
		text = getText(files)
	text, links = getAmudimAndLinks(text)
	postRif(amudim, links)
	