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
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from data_utilities import util, sanity_checks
from data_utilities.sanity_checks import TagTester
from functions import *
from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *


def dealWithPerek(line, current_perek):
	perek_info = line.replace(u"@00פרק ", u"").replace(u'@00פ"', u'')
	poss_perek = getGematria(perek_info)
	if poss_perek - current_perek <= 0:
		print 'pereks not right'
		pdb.set_trace()
	current_perek = poss_perek
	return current_perek


def dealWithMishnah(line, current_mishnah):
	mishnah_info = line.split(" ", 1)[0]
	poss_mishnah = getGematria(mishnah_info)
	if poss_mishnah - current_mishnah <= 0:
		print 'mishnah not right'
		pdb.set_trace()
	current_mishnah = poss_mishnah
	return current_mishnah


def getText(line):
	if line.find("@00") == -1 and line.find("@99") == -1 and len(line) > 10:
		reg = u'@22.*?[\u05d0-\u05ea]+.*?'
		match = re.findall(reg, line)
		if len(match) > 0:
			line = line.replace(match[0] + " ", "").replace(match[0], "")
		line = line.replace("@11", "").replace("@33", "")
		line = removeAllStrings(["@", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"], line)
		if line.find(".") >= 0:
			dh, comment = line.split(".", 1)
			line = "<b>" + dh + "</b>." + comment			
		return line
	return ""



def post_index_TYT(enTitle, has_intro):
	enTitle = "Mishnah "+enTitle if enTitle != "Avot" else "Pirkei Avot"
	heTitle = getHebrewTitle(enTitle) if enTitle != "Avot" else u"פרקי אבות"

	root = SchemaNode()
	root.add_title("Tosafot Yom Tov on "+enTitle, "en", primary=True) 
	root.add_title(u"תוספות יום טוב על "+heTitle, "he", primary=True)
	root.key = "tosafot_yom_tov"+enTitle


	if has_intro == True:
		intro_node = JaggedArrayNode()
		intro_node.add_title(enTitle.replace("_"," ")	+", Introduction", "en", primary=True)
		intro_node.add_title(heTitle+u", הקדמה", "he", primary=True)
		intro_node.key = 'intro'+enTitle
		intro_node.sectionNames = ["Paragraph"]
		intro_node.depth = 1
		intro_node.addressTypes = ["Integer"]
		root.append(intro_node)
	main_node = JaggedArrayNode()
	main_node.default = True
	main_node.key = "default"
	main_node.sectionNames = ["Perek", "Mishnah", "Comment"]
	main_node.depth = 3
	main_node.addressTypes = ["Integer", "Integer", "Integer"]
	root.append(main_node)
		
	root.validate()

	index = {
	    "title": "Tosafot Yom Tov on "+enTitle,
	    "categories": ["Commentary2", "Mishnah", "Tosafot Yom Tov"],
	    "schema": root.serialize()
	}

	post_index(index)


def post_text_TYT(masechet, text):
	masechet = "Mishnah_"+masechet if masechet != "Avot" else "Pirkei_Avot"
	for perek in text:
		text[perek] = convertDictToArray(text[perek])
		text_array = convertDictToArray(text)
		send_text = {
			"text": text_array,
			"versionTitle": "http://www.daat.ac.il/daat/vl/tohen.asp?id=202",
			"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002036659",
			"language": "he"
		}
	post_text("Tosafot Yom Tov on "+masechet, send_text)
	links = []
	for perek in range(len(text_array)):
		for mishnah in range(len(text_array[perek])):
			mishnah_link = masechet+"."+str(perek+1)+"."+str(mishnah+1)
			TYT_link = "Tosafot_Yom_Tov_on_"+masechet+"."+str(perek+1)+"."+str(mishnah+1)
			links.append({'refs': [mishnah_link, TYT_link], 'type': 'commentary', 'auto': 'True', 'generated_by': 'TYT'})
	post_link(links)

def parseFile(file):
	text = {}
	current_perek = 0
	for line in file:
		line = line.decode('utf-8')
		if line.find("@00") >= 0:
			current_perek = dealWithPerek(line, current_perek)
			text[current_perek] = {}
			current_mishnah = 0
		elif line.find("@22") >= 0:
			current_mishnah = dealWithMishnah(line, current_mishnah)
			text[current_perek][current_mishnah] = []

		this_line = getText(line)
		if len(this_line) > 0:
			text[current_perek][current_mishnah].append(this_line)

	return text


if __name__ == "__main__":
	not_yet = True
	until_this_one = "niddah.txt"
	masechet_has_intro = {}
	for file in glob.glob(u"*.txt"):
		if file.find("intro") >= 0:
			masechet_has_intro[file.replace("_intro", "")] = True
		else:
			masechet_has_intro[file.replace("_intro", "")] = False


	for file in glob.glob(u"*.txt"):
		if file.find("intro") == -1:
			if not_yet and file.find(until_this_one) == -1:
				continue
			else:
				not_yet = False 
			open_file = open(file)
			masechet = file.replace(".txt", "").replace("_", " ").title()
			has_intro = masechet_has_intro[file]
			post_index_TYT(masechet, has_intro)
			text = parseFile(open_file)
			post_text_TYT(masechet, text)
			

			