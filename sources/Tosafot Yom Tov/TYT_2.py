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



def flagBadChars(line, chars, masechet, current_perek, current_mishnah):
	flagged = open('flagged', 'a')
	for char in chars:
		if char != '#' and char != '!':
			flagged.write(masechet + ', '+str(current_perek)+', '+str(current_mishnah)+' : ' + char.encode('utf-8') + '\n')
	flagged.close()



def addITags(lines, chars_arr):
	new_lines = []
	count = 0
	for line_n, line in enumerate(lines):
		chars = chars_arr[line_n]
		bad_char = '@'
		desired_chars = []
		if '#' in line:
			desired_chars = [char for char in chars if char == '#']
			bad_char = '#'
		elif '!' in line:
			desired_chars = [char for char in chars if char == '!']
			bad_char = '!'

		for i in range(len(desired_chars)):
			i_tag = """<i data-commentator="R' Akiva Eiger" data-order='"""+str(i+1+count)+"'></i>"
			line = line.replace(bad_char, i_tag, 1)
		count += len(desired_chars)
		new_lines.append(line)
	return new_lines


def getText(line, masechet, current_perek, current_mishnah):
	good_list = ['*', '.', '%', ',', '"', "'", ':', '(', ')', '[', ']', u'׳', u'\u2003', u'\u05f4', u'\u202a', u'\u202c', u"’"] + re.findall(u'[\u05b0-\u05c4]', line)
	if line.find("@00") == -1 and line.find("@99") == -1 and len(line) > 10:
		reg = u'@22.*?[\u05d0-\u05ea]+.*?'
		match = re.findall(reg, line)
		if len(match) > 0:
			line = line.replace(match[0] + " ", "").replace(match[0], "")
		line = line.replace("@11", "").replace("@33", "")
		line = removeAllStrings(line)
		other_poss_chars = re.findall(u'[^\u05d0-\u05ea\s]', line)
		other_actual_chars = [el for el in other_poss_chars if el not in good_list]
		flagBadChars(line, other_actual_chars, masechet, current_perek, current_mishnah)
		if line.find(".") >= 0:
			dh, comment = line.split(".", 1)
			line = "<b>" + dh + "</b>." + comment			
		return line, other_actual_chars
	return "", ""



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
			"versionTitle": "Mishnah, ed. Romm, Vilna 1913",
			"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002036659",
			"language": "he"
		}
	post_text("Tosafot Yom Tov on "+masechet, send_text)
	'''
	links = []
	for perek in range(len(text_array)):
		for mishnah in range(len(text_array[perek])):
			mishnah_link = masechet+"."+str(perek+1)+"."+str(mishnah+1)
			for comment in range(len(text_array[perek][mishnah])):
				TYT_link = "Tosafot_Yom_Tov_on_"+masechet+"."+str(perek+1)+"."+str(mishnah+1)+"."+str(comment+1)
				links.append({'refs': [mishnah_link, TYT_link], 'type': 'commentary', 'auto': 'True', 'generated_by': 'TYT'})
	post_link(links)
	'''


def parseFile(file, masechet):
	text = {}
	current_perek = 0
	lines_current_mishnah = []
	other_chars_current_mishnah = []
	for line in file:
		line = line.decode('utf-8')
		if len(line.replace(" ", "").replace("\n", "")) == 0:
			continue
		if line.find("@00") >= 0:
			if len(lines_current_mishnah) > 0:
				lines_current_mishnah = addITags(lines_current_mishnah, other_chars_current_mishnah)
				text[current_perek][current_mishnah] = lines_current_mishnah

			lines_current_mishnah = []
			other_chars_current_mishnah = []
			current_perek = dealWithPerek(line, current_perek)
			text[current_perek] = {}
			current_mishnah = 0
			continue
		elif line.find("@22") >= 0:
			if len(lines_current_mishnah) > 0:
				lines_current_mishnah = addITags(lines_current_mishnah, other_chars_current_mishnah)
				text[current_perek][current_mishnah] = lines_current_mishnah

			current_mishnah = dealWithMishnah(line, current_mishnah)
			text[current_perek][current_mishnah] = []
			lines_current_mishnah = []
			other_chars_current_mishnah = []

		this_line, other_chars = getText(line, masechet, current_perek, current_mishnah)
		
		if len(this_line) > 0:
			lines_current_mishnah.append(this_line)
			other_chars_current_mishnah.append(other_chars)
		prev_line = line
	return text



if __name__ == "__main__":
	not_yet = True
	until_this_one = "arakhin.txt"
	masechet_has_intro = {}
	for file in glob.glob(u"*.txt"):
		if file.find("intro") >= 0:
			masechet_has_intro[file.replace("_intro", "")] = True
		else:
			masechet_has_intro[file.replace("_intro", "")] = False

	for file in glob.glob(u"*.txt"):
		if file.find("intro") == -1:
			print file
			if not_yet and file.find(until_this_one) == -1:
				continue
			else:
				not_yet = False 
			open_file = open(file)
			masechet = file.replace(".txt", "").replace("_", " ").title()
			has_intro = masechet_has_intro[file]
			#post_index_TYT(masechet, has_intro)
			text = parseFile(open_file, masechet)
			post_text_TYT(masechet, text)
		'''
		elif file.find("intro") >= 0:
			masechet = file.replace("_intro.txt", "").replace("_", " ").title()
			open_file = open(file)
			text = getText(open_file)
			send_text = {
			"text": [text],
			"versionTitle": "Mishnah, ed. Romm, Vilna 1913",
			"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002036659",
			"language": "he"
			}
			if masechet == "Avot":
				post_text("Tosafot Yom Tov on Pirkei "+masechet+",_Pirkei "+masechet+",_Introduction", send_text)
			else:
				post_text("Tosafot Yom Tov on Mishnah "+masechet+",_Mishnah "+masechet+",_Introduction", send_text)
			
		'''
			