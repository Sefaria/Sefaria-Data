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

	root = JaggedArrayNode()
	root.add_title("Ritva on "+enTitle, "en", primary=True) 
	root.add_title(u'ריטב"א על '+heTitle, "he", primary=True)
	root.key = "Ritva+"+enTitle
	root.sectionNames = ["Daf", "Comment"]
	root.depth = 2
	root.addressTypes = ["Talmud", "Integer"]

		
	root.validate()

	index = {
	    "title": "Ritva on "+enTitle,
	    "categories": ["Talmud", "Ritva"],
	    "schema": root.serialize()
	}

	post_index(index)


def dealWithDaf(line, current_daf):
	orig_line = line
	line = line.replace("@22", "").replace('ע"א','').replace('דף', '').replace('\r', '').replace(' ', '').replace('.', '')
	if len(line.replace('ע"ב','').replace(' ','').replace('[', '').replace(']', '').replace('(', '').replace(')', '')) == 0:
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
	dhs = {}
	current_daf = 0
	for line in file:
		line = line.replace('\n', '')
		if line.find("@11") >= 0:
			line = line.replace("@11", "").replace("@33", "")
			dh, comment, found = getDHComment(line)
			if current_daf in dhs:
				dhs[current_daf].append(dh)
			else:
				dhs[current_daf] = []
			if found == True:
				line = "<b>"+dh+"</b>"+comment
			if len(header) > 0:
				line = "<b>"+header+"</b><br>"+line
				header = ""
			text[current_daf].append(line)
		elif line.find("@22") >= 0:
			current_daf = dealWithDaf(line, current_daf)
			text[current_daf] = []
		elif line.find("@00") >= 0:
			header = line.replace("@00", "")
	return text, dhs


def getDHComment(each_line):
	found = True
	if each_line.find("כו'") >= 0:
		dh, comment = each_line.split("כו'", 1)
		dh += "כו'"
	elif each_line.find(".") >= 0:
		dh, comment = each_line.split(".", 1)
		dh += "."
	else:
		found = False
		dh, comment = splitText(each_line, 10)
	return dh, comment, found


def splitText(text, num_words):
	num_words = num_words if len(text.split(" ")) > 20 else len(text.split(" "))/4 
	text_arr = text.split(" ", num_words)
	before = " ".join(text_arr[0:num_words])
	after = text_arr[num_words]
	return before, after


def match_and_link(dhs, masechet):
	match = Match(in_order=True, min_ratio=80, guess=False, range=True, can_expand=False)
	links = []
	for daf in dhs:
		try:
			talmud_text = get_text_plus(masechet+"."+AddressTalmud.toStr("en", daf))['he']
		except:
			pdb.set_trace()
		result = match.match_list(dhs[daf], talmud_text)
		for line in result:
			talmud_range = result[line].replace("0:", "")
			Ritva_end = "Ritva on "+masechet+"."+str(AddressTalmud.toStr("en", daf))+"."+str(line)
			talmud_end = masechet + "." + AddressTalmud.toStr("en", daf) + "." + talmud_range
			links.append({'refs': [Ritva_end, talmud_end], 'type': 'commentary', 'auto': 'True', 'generated_by': masechet+"Ritva"})
	post_link(links)


if __name__ == "__main__":
	versionTitle = {}
	versionTitle['Sukkah'] = 'Chiddushei HaRashba, Sheva Shitot, Warsaw, 1883.'
	versionTitle['Berakhot'] = 'Berakhah Meshuleshet, Warsaw, 1863.'
	versionTitle['Moed Katan'] = 'Chidushi HaRitva, Amsterdam, 1729.'
	versionTitle['Yoma'] = 'Chiddushei HaRitva, Berlin, 1860.'
	versionTitle['Megillah'] = 'Kodshei David, Livorno, 1792.'
	versionTitle['Rosh Hashanah'] = 'Chiddushei HaRitva, Königsberg, 1858.'
	versionTitle['Taanit'] = 'Chidushi HaRitva, Amsterdam, 1729.'
	versionTitle['Niddah'] = 'Hidushe ha-Ritba al Nidah; Wien 1868.'
	files = ["Sukkah", "Berakhot", "Moed Katan", "Yoma", "Megillah", "Rosh Hashanah", "Taanit", "Niddah"]
	not_yet = True
	until_this_one = "Megillah"
	for file in files:
		if file == until_this_one:
			not_yet = False
		if not_yet:
			continue
		createIndex(file)
		text, dhs = parse(open(file+".txt"))
		text_array = convertDictToArray(text)
		send_text = {
		"text": text_array,
		"language": "he",
		"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001201716",
		"versionTitle": versionTitle[file]
		}
		post_text("Ritva on "+file, send_text)
		match_and_link(dhs, file)