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
from functions import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud


def replaceWithOrder(line, at):
	count = 1
	before_marker = at[0:2]
	after_marker = at[2:]
	while line.find(at)>=0:
		pos = line.find(at)
		line_before = line[0:pos]
		line_after = line[pos+4:]
		replace_with = before_marker+numToHeb(count).encode('utf-8')+after_marker
		try:
			line = line_before+replace_with+line_after
		except:
			pdb.set_trace()
		count+=1
	return line

def replaceWithHTMLTags(line, helek, siman_num):
	commentaries = ["Drisha", "Prisha", "Darchei Moshe", "Hagahot", "Bi", "Bach", "Mystery"]
	line = line.decode('utf-8')
	line = line.replace('%(', '(%')
	matches_array = [re.findall(u"\[[\u05D0-\u05EA]{1,4}\]", line), re.findall(u"\([\u05D0-\u05EA]{1,4}\)", line), 
						re.findall(u"\(%[\u05D0-\u05EA]{1,4}\)", line), re.findall(u"\s#[\u05D0-\u05EA]{1,4}", line), 
						re.findall(u"\{[\u05D0-\u05EA]{1,4}\}",line), re.findall(u"\|[\u05D0-\u05EA]{1,4}\|", line),
						re.findall(u"<[\u05D0-\u05EA]{1,4}>",line)]
	for commentary_count, matches in enumerate(matches_array):
		how_many_shams = 0
		for order_count, match in enumerate(matches):
			#if commentaries[commentary_count] == "Prisha" and helek == "Orach Chaim" and str(siman_num) == '2':
			#	pdb.set_trace()
			if match == u"(שם)" or match == u"[שם]":
				how_many_shams += 1
				continue
			HTML_tag =  '<i data-commentator="'+commentaries[commentary_count]+'" data-order="'+str(order_count+1-how_many_shams)+'"></i>'
			line = line.replace(match, HTML_tag)
		#if helek == "Orach Chaim" and siman_num == 144 and commentaries[commentary_count]=="Prisha":
		#	pdb.set_trace()
		csvwriter.writerow([helek, commentaries[commentary_count], siman_num, len(matches)-how_many_shams])
	return line			


def create_indexes(eng_helekim, heb_helekim):
  tur = SchemaNode()
  tur.add_title("Tur", 'en', primary=True)
  tur.add_title(u"טור", 'he', primary=True)
  tur.key = 'tur'
  
  for count, helek in enumerate(eng_helekim):
	  helek_node = JaggedArrayNode()
  	  helek_node.add_title(helek, 'en', primary=True)
  	  helek_node.add_title(heb_helekim[count], 'he', primary=True)
  	  helek_node.key = helek
  	  helek_node.depth = 2
  	  helek_node.addressTypes = ["Integer", "Integer"]
  	  helek_node.sectionNames = ["Siman", "Paragraph"]
  	  tur.append(helek_node)
  tur.validate()
  index = {
	"title": "Tur",
	"categories": ["Halakhah"],
	"schema": tur.serialize()
	}
  post_index(index)

def parse_text(at_66, at_77, at_88, helekim, files_helekim):
  for count, helek in enumerate(helekim):
	f = open(files_helekim[count])
	current_siman = 0
	append_to_next_line= False
	prev_hilchot_topic = ""
	text[helek] = {}
	for line in f:
		actual_line = line
		line = line.replace('\n','')
		if len(line)==0:
			continue
		if (len(line)<=12 and line.find("@22")>=0) or (line.find(' ')==line.rfind(' ')):
			append_to_next_line = True
			appending = line
			continue
		if append_to_next_line:
			#print appending+line
			append_to_next_line = False
			line = appending + line
		first_word_66 = -1
		first_word_77 = -1
		first_word_88 = -1
		siman_header = False
		if line.find("@22")>=0 or (line.find("@00")>=0 and len(line)>200):
			siman_header = True
			first_space = line.find(' ')
			first_word = line[0:first_space]
			first_word_66 = first_word.find("@66")
			first_word_77 = first_word.find("@77")
			first_word_88 = first_word.find("@88")
			first_word = first_word.replace("@22","").replace("@77","").replace("@66","").replace("@11","").replace("@88","").replace("@00","")
			this_siman = getGematria(first_word)
			if this_siman != current_siman + 1 and this_siman != current_siman+2:
				print 'siman off'
				print this_siman
				print current_siman
				print helek
				print line
			line_wout_first_word = line[first_space+1:]
			second_word = line_wout_first_word[0:line_wout_first_word.find(' ')]
			second_gematria = getGematria(second_word)
			current_siman = this_siman
			line = line[first_space+1:]
		if first_word_66 >= 0:
			line = "@66"+line
		if first_word_77 >= 0:
			line = "@77"+line
		if first_word_88 >= 0:
			line = "@88"+line
		line = line.replace("@66", at_66)
		line = line.replace("@77", at_77)
		line = line.replace("@88", at_88)
		line = replaceWithOrder(line, at_66)
		line = replaceWithOrder(line, at_77)
		line = replaceWithOrder(line, at_88)
		line = line.replace("@33","").replace("@11","").replace("@22","").replace("@00","").replace("@44","").replace("@55","").replace("@99","").replace("@98","").replace("@89","")
		if line.find("@")>=0:
			pdb.set_trace()		
		if current_siman not in text[helek]:
			text[helek][current_siman] = [line]
			line = replaceWithHTMLTags(line, helek, current_siman)
		else:
			text[helek][current_siman][0] = text[helek][current_siman][0]+"<br>"+line
		if second_gematria - this_siman == 1:
			text[helek][second_gematria] = ["ראו סימן "+str(current_siman)]
			current_siman = second_gematria
		prev_line = actual_line

if __name__ == "__main__":
	import csv
	csvf = open('comments_per_siman.csv', 'wb')
	global csvwriter
	csvwriter = csv.writer(csvf, delimiter=',')
	global text 
	text = {}
	global hilchot_topic 
	hilchot_topic = {}
	eng_helekim = ["Yoreh Deah", "Choshen Mishpat", "Even HaEzer", "Orach Chaim"]
	heb_helekim = [u"יורה דעה", u"חושן משפט", u"אבן העזר", u"אורח חיים"]
	at_66 = " {} "
	at_77 = " || "
	at_88 = " <> "
	files_helekim = ["Yoreh Deah/tur yoreh deah.txt", "Choshen Mishpat/tur choshen mishpat.txt", "Even HaEzer/tur even haezer.txt", "OrachChaim/tur orach chaim.txt"]
	#create_indexes(eng_helekim, heb_helekim)
	parse_text(at_66, at_77, at_88, eng_helekim, files_helekim)
	for helek in eng_helekim:
		send_text = {
			"text": convertDictToArray(text[helek]),
			"language": "he",
			"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001935970",
			"versionTitle": "Vilna, 1923"
		}
		#post_text("Tur,_"+helek, send_text)
	
