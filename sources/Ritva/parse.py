# -*- coding: utf-8 -*-
import urllib2
import urllib
from urllib2 import URLError, HTTPError
import json 
import pdb
import glob
import os
import sys
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from data_utilities import util, sanity_checks
from data_utilities.sanity_checks import TagTester
from functions import *
from local_settings import *
from match import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud


def createIndex(enTitle):
	heTitle = getHebrewTitle(enTitle)

	root = SchemaNode()
	root.add_title("Ritva on "+enTitle, "en", primary=True) 
	root.add_title(u' ריטב"א'+heTitle, "he", primary=True)
	root.key = "ritva"+enTitle

	main_node = JaggedArrayNode()
	main_node.default = True
	main_node.key = "default"
	main_node.sectionNames = ["Daf", "Comment"]
	main_node.depth = 2
	main_node.addressTypes = ["Integer", "Integer"]
	root.append(main_node)
		
	root.validate()

	index = {
	    "title": "Ritva on "+enTitle,
	    "categories": ["Commentary2", "Talmud", "Ritva"],
	    "schema": root.serialize()
	}

	post_index(index)


def dealWithDaf(line, current_daf):
	print line
	orig_line = line
	line = line.replace("@22", "").replace('ע"א','').replace('דף', '')
	if len(line.replace('ע"ב','').replace(' ','')) == 0:
		return current_daf + 1
	elif line.find('ע"ב') >= 0:
		line = line.replace('ע"ב', '')
		poss_daf = getGematria(line) * 2
		if poss_daf <= current_daf:
			print 'daf prob'
			pdb.set_trace()
		return poss_daf
	else:
		poss_daf = (getGematria(line) * 2) - 1
		if poss_daf <= current_daf:
			print 'daf prob'
			pdb.set_trace()
		return poss_daf


def parse(file):
	header = ""
	text = {}
	current_daf = 0
	for line in file:
		line = line.replace('\n', '')
		if line.find("@11") >= 0:
			line = line.replace("@11", "").replace("@33", "")
			if len(header) > 0:
				line = "<b>"+header+"</b><br>"+line
				header = ""
			text[current_daf].append(line)
		elif line.find("@22") >= 0:
			current_daf = dealWithDaf(line, current_daf)
			text[current_daf] = []
		elif line.find("@00") >= 0:
			header = line.replace("@00", "")
	return text


def splitText(text, num_words):
	text_arr = text.split(" ", num_words)
	before = " ".join(text_arr[0:num_words])
	after = text_arr[num_words]
	return before, after


def match_and_link(text, masechet):
	match = Match(in_order=True, min_ratio=80, guess=False, range=True, can_expand=False)
	for daf_count, daf in enumerate(text):
		dhs = []
		comments = []
		for each_line in daf:
			if each_line.find("כו'") >= 0:
				dh, comment = each_line.split("כו'", 1)
			elif each_line.find(".") >= 0:
				dh, comment = each_line.split(".", 1)
			else:
				dh, comment = splitText(each_line, 10)
			dhs.append(dh)
			comments.append(comment)
		pdb.set_trace()
		talmud_text = get_text_plus(masechet+"."+AddressTalmud.toStr("en", daf_count+3))['he']
		result = match.match_list(dhs, talmud_text)

if __name__ == "__main__":
	versionTitle = {}
	versionTitle['Sukkah'] = 'Chiddushei HaRashba, Sheva Shitot, Warsaw, 1883.'
	versionTitle['Berakhot'] = 'Berakhah Meshuleshet, Warsaw, 1863.'
	versionTitle['Megillah'] = 'Kodshei David, Livorno, 1792.'
	versionTitle['Moed Katan'] = 'f'
	versionTitle['Yoma'] = 'Chidushei HaRitva, Berlin, 1860.'
	versionTitle['Rosh Hashanah'] = 'Chiddushei HaRitva, Königsberg, 1858.'
	versionTitle['Taanit'] = 'Chidushi HaRitva, Amsterdam, 1729.'
	versionTitle['Niddah'] = 'f'
	files = ["Sukkah", "Berakhot", "Megillah", "Moed Katan", "Yoma", "Rosh Hashanah", "Taanit", "Niddah"]
	for file in files:
		#createIndex(file)
		text = parse(open(file+".txt"))
		text = convertDictToArray(text)
		send_text = {
		"text": text,
		"language": "he",
		"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001201716",
		"versionTitle": versionTitle[file]
		}
		#post_text("Ritva on "+file, send_text)
		match_and_link(text, file)