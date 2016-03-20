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

#pattern = re.compile('@\d\d\s?[\[\(].*?[\]\)]')
#pattern = re.compile('(@\d\d)+[\[\(].{1,4}[\]\)]')
pattern =  re.compile('(@?\d\d)+[\[\(][^&]{1,4}[\]\)]')
curr_siman = 0
curr_seif_katan = 0
text = {}
 
def create_indexes(eng_helekim, heb_helekim, eng_title, heb_title):
  #helek, siman, seif_katan
  commentary = SchemaNode()
  commentary.add_title(eng_title, 'en', primary=True)
  commentary.add_title(heb_title, 'he', primary=True)
  commentary.key = eng_title
	
  for count, helek in enumerate(eng_helekim):
	  helek_node = JaggedArrayNode()
  	  helek_node.add_title(helek, 'en', primary=True)
  	  helek_node.add_title(heb_helekim[count], 'he', primary=True)
  	  helek_node.key = helek
  	  helek_node.depth = 3
  	  helek_node.addressTypes = ["Integer", "Integer", "Integer"]
  	  helek_node.sectionNames = ["Siman", "Seif Katan", "Paragraph"]
  	  commentary.append(helek_node)
  commentary.validate()
  index = {
	"title": eng_title,
	"categories": ["Halakhah", "Tur"],
	"schema": commentary.serialize()
	}
  post_index(index)
	
def checkCSV(helek, commentator, siman, num_comments, prev_line):
	csvf = open('comments_per_siman.csv', 'r')
	csvreader = csv.reader(csvf, delimiter=',')
	first_words = " ".join(prev_line.split(" ")[0:4])
	for row in csvreader:
		if helek == row[0] and commentator == row[1] and str(siman) == row[2]:
			#if helek == "Orach Chaim" and commentator == "Prisha" and siman==135:
			#	pdb.set_trace()
			if commentator == "Drisha" and helek == "Choshen Mishpat":
				continue
			if abs(num_comments-int(row[3])) > 0 and abs(num_comments-int(row[3])) <= 5:
				num_comments_mismatch_small.write(helek.replace(" ","_")+";"+commentator+";Siman:"+str(siman)+";"+commentator+"_Count;"+str(num_comments)+";Tur_Count:"+row[3]+';First_Words_Prev_Line:'+first_words+'\n')
			elif abs(num_comments-int(row[3])) > 5:
				num_comments_mismatch_big.write(helek.replace(" ","_")+";"+commentator+";Siman:"+str(siman)+";"+commentator+"_Count;"+str(num_comments)+";Tur_Count:"+row[3]+';First_Words_Prev_Line:'+first_words+'\n')
	csvf.close()
	
def dealWithTwoSimanim(text):
	if text[0] == ' ':
		text = text[1:]
	if text[len(text)-1] == ' ':
		text = text[:-1]
	if len(text.split(" "))>1:
		if len(text.split(" ")[0]) > 0 and len(text.split(" ")[1]) > 0:
			text = text.split(" ")[0]
	return text


def divideUpLines(text, commentator):
	
	tag = " "
	text_array = []
	if commentator == "Bach":
		tag = "@77"
	elif commentator == "Bi" or commentator == "Beit Yosef":
		tag = "@66"
	if text.find(tag)==0:
		text = text.replace(tag,"", 1)
	text_array = text.split(tag)
	for i in range(len(text_array)):
		text_array[i] = [text_array[i]]
	return text_array
	
def parse_text(helekim, files, commentator):
  store_this_line = ""
  bach_bi_lines = ""
  for count, helek in enumerate(helekim):
    curr_siman = 0
    curr_seif_katan = 0
    f = open(files[count])
    text[helek] = {}
    seif_list = []
    actual_seif_katan = 0
    for line in f:
  	  actual_line = line
  	  line = line.replace("\n", "")
  	  #deal with case where seif katan marker is separated from comment and is on line before comment
  	  if len(store_this_line)>0:
  	  	line = store_this_line+line
  	  	store_this_line = ""
  	  if len(line)<15 and line.find("@22")==-1:
  	  	store_this_line = line
  	  	continue
  	  if len(line) < 4:
  	  	continue
  	  if line[0] == ' ':
		line = line[1:]
	  #deal with strange cases first
	  if (line.find("@22סי'")>=0 or line.find("@22סי")>=0) and len(line.split(" "))>4: #ONLY DRISHA ON YOREH DEAH
		  nothing, siman, line = line.split("@",2)
		  siman = siman.replace("22סי'","").replace("22סי","")
		  siman = dealWithTwoSimanim(siman)
		  poss_siman = getGematria(siman)  
		  if poss_siman == curr_siman - 2 and siman.find('ה')>=0:
		  		poss_siman += 3
		  elif poss_siman <= curr_siman:
		  		print 'siman issue'
		  		siman_file.write(helek+","+commentator+","+str(poss_siman)+","+str(curr_siman)+","+actual_line+"\n")		  				
		  if curr_siman > 0:
				checkCSV(helek, commentator, curr_siman, len(text[helek][curr_siman]), prev_line)
		  curr_siman = poss_siman
		  curr_seif_katan = 0
		  actual_seif_katan = 0
		  text[helek][curr_siman] = {}
		  seif_list = []
		  line = "@"+line
	  if (line.find("@66@22")>=0 or line.find("@77@22")>=0) and len(line.split(" "))>4:  #ONLY BEIT YOSEF and BACH ON YOREH DEAH
		  beg, line = line.split(" ", 1)
		  beg = beg.replace("@66@22","")
		  beg = dealWithTwoSimanim(beg)
		  poss_siman = getGematria(beg)
		  if poss_siman == curr_siman - 2 and beg.find('ה')>=0:
		  		poss_siman += 3
		  elif poss_siman <= curr_siman:
		  		print 'siman issue'
		  		siman_file.write(helek+","+commentator+","+str(poss_siman)+","+str(curr_siman)+","+actual_line+"\n")
		
		  if len(bach_bi_lines)>0 and commentator == "Bach" or commentator == "Bi":
			  text[helek][curr_siman] = divideUpLines(bach_bi_lines, commentator)
			  
		  if curr_siman > 0:
				checkCSV(helek, commentator, curr_siman, len(text[helek][curr_siman]), prev_line)  
		  bach_bi_lines = ""
		  curr_siman = poss_siman
		  curr_seif_katan = 1
		  actual_seif_katan = 1
		  text[helek][curr_siman] = {}
		  seif_list = []  
		  seif_list.append(curr_seif_katan)
		  bach_bi_lines += line
		  continue
	  #now process three typical cases: Siman header, Comment with Seif Katan marker, Comment without Seif Katan marker	
	  if pattern.match(line):
		seif_katan = pattern.match(line).group(0)
		temp_arr = re.split('\d\d', seif_katan)
		seif_katan = temp_arr[len(temp_arr)-1]
		poss_seif_katan = getGematria(removeAllStrings(["[","]","(",")"], seif_katan))
		if poss_seif_katan == curr_seif_katan-2 and seif_katan.find('ה')>=0:
			poss_seif_katan += 3
		elif poss_seif_katan < curr_seif_katan:
			seif_file.write(helek+","+commentator+","+str(curr_siman)+","+str(poss_seif_katan)+","+str(curr_seif_katan)+","+actual_line+"\n")
		if poss_seif_katan in seif_list:
			seif_katan = pattern.match(line).group(0)
			marked_seif_katan = seif_katan[0:len(seif_katan)-1]+'*'+seif_katan[len(seif_katan)-1]
			line = line.replace(seif_katan, marked_seif_katan)
		else:
			seif_katan = pattern.match(line).group(0)
			add_after = ""
			if seif_katan.find("@77")>=0:
				add_after += "@77"
			if seif_katan.find("@66")>=0:
				add_after += "@66"
			if seif_katan.find("@88")>=0:
				add_after += "@88"
			line = line.replace(seif_katan, "")
			line = add_after + line
			seif_list.append(poss_seif_katan)
		
		bach_bi_lines += line
		line = removeAllStrings(["@11", "@22","@33", "@44", "@55", "@66", "@77", "@87","@88","@89", "@98"], line)

		curr_seif_katan = poss_seif_katan
		actual_seif_katan += 1
		curr_seif_katan_line = actual_line
		if line.find("@")>=0:
			print '@'
			pdb.set_trace()
		text[helek][curr_siman][actual_seif_katan] = [line]	
	  elif line.find("@22סי'")>=0 or (line.find("@22")<4 and line.find("@22")>=0 and len(line.split(" ")) < 4):
			line = line.replace("@22סי' ", "").replace("@22ס' ","").replace("@22סי ","")
			line = line.replace("@22", "").replace("@66","").replace("@77","")
			if len(bach_bi_lines)>0 and commentator == "Bach" or commentator == "Bi":
				text[helek][curr_siman] = divideUpLines(bach_bi_lines, commentator)
			
			if curr_siman > 0:
				checkCSV(helek, commentator, curr_siman, len(text[helek][curr_siman]), prev_line)
			if len(line) > 0:
				line = dealWithTwoSimanim(line)
				poss_siman = getGematria(line)
			else:
				poss_siman += 1
			if poss_siman == curr_siman - 2 and line.find('ה')>=0:
				poss_siman += 3
			elif poss_siman <= curr_siman:
				print 'siman issue'
				siman_file.write(helek+","+commentator+","+str(poss_siman)+","+str(curr_siman)+","+actual_line+"\n")
			
			prev_siman = curr_siman
			bach_bi_lines=""
			curr_siman = poss_siman
			curr_seif_katan = 0
			actual_seif_katan = 0
			seif_list = []
			text[helek][curr_siman] = {}
	  else: #just add it to current seif katan	
		if commentator == "Prisha" or commentator == "Drisha":
			line = removeAllStrings(["@", "1", "2", "3", "4", "5", "6", "7", "8", "9"], line)
			if line.find("@")>=0:
				print line.find("@")
				pdb.set_trace()
			if len(text[helek][curr_siman]) == 0:
				text[helek][curr_siman][actual_seif_katan] = [line]
			else:
				text[helek][curr_siman][actual_seif_katan][0] += "<br>"+line
		else:
			bach_bi_lines += line
	  prev_line = actual_line
	  
def post_commentary(commentator):
	return 'hi'
	'''
	for helek in text:
		print helek
		for siman in text[helek]:
			print helek
			print siman
			for seif_katan in text[helek][siman]:
				send_text = {
				"text": text[helek][siman][seif_katan][0],
				"language": "he",
				"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001935970",
				"versionTitle": "Vilna, 1923"
				}
				post_text(commentator+",_"+helek+",_"+str(siman)+"."+str(seif_katan)+".1", send_text)
	
	for helek in text:
		if helek != "Even HaEzer" and helek != "Orach Chaim":
			continue
		print helek
		for siman in text[helek]:
			text[helek][siman] = convertDictToArray(text[helek][siman])
		text_to_post = convertDictToArray(text[helek])
		send_text = {
			"text": text_to_post,
			"language": "he",
			"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001935970",
			"versionTitle": "Vilna, 1923"
			}
  		post_text(commentator+",_"+helek, send_text)
	'''
if __name__ == "__main__":
  import csv
  global siman_file
  global seif_file    
  siman_file = open('siman_probs.csv', 'a')
  seif_file = open('seif_probs.csv', 'a')
  num_comments_mismatch_small = open('num_comments_mismatch_small_diff.csv', 'a')
  num_comments_mismatch_big = open('num_comments_mismatch_big_diff.csv', 'a')
  eng_helekim = ["Orach Chaim", "Yoreh Deah", "Even HaEzer", "Choshen Mishpat"]
  heb_helekim = [u"אורח חיים", u"יורה דעה", u"אבן העזר", u"חושן משפט"]
  if sys.argv[1] == 'Drisha':
  	files_helekim = ["OrachChaim/drisha orach chaim helek a.txt", "yoreh deah/drisha yoreh deah.txt",
   "Even HaEzer/drisha even haezer.txt", "Choshen Mishpat/drisha choshen mishpat.txt"]
  	create_indexes(eng_helekim, heb_helekim, "Drisha", u"דרישה")
  	parse_text(eng_helekim, files_helekim, "Drisha")
  	print 'here****'
  	post_commentary("Drisha")
  elif sys.argv[1] == 'Prisha':
  	files_helekim = ["OrachChaim/prisha orach chaim.txt", "yoreh deah/prisha yoreh deah.txt",
   "Even HaEzer/prisha even haezer.txt", "Choshen Mishpat/prisha choshen mishpat.txt"]
  	create_indexes(eng_helekim, heb_helekim, "Prisha", u"פרישה")
  	parse_text(eng_helekim, files_helekim, "Prisha")
  	post_commentary("Prisha")
  elif sys.argv[1] == 'Bi':
  	files_helekim = ["OrachChaim/beit yosef orach chaim helek a.txt", "yoreh deah/beit yosef yoreh deah.txt", "Even HaEzer/Bi Even HaEzer.txt",
  	"Choshen Mishpat/Bi choshen mishpat.txt"]
  	#create_indexes(eng_helekim, heb_helekim, "Bi", u'ב"י')
  	parse_text(eng_helekim, files_helekim, "Bi")
  	post_commentary("Bi")
  elif sys.argv[1].find("Bach")>=0:
    files_helekim = ["OrachChaim/bach orach chaim helek a.txt", "yoreh deah/bach yoreh deah.txt", "Even HaEzer/bach even haezer.txt",
    "Choshen Mishpat/bach choshen mishpat.txt"]
    create_indexes(eng_helekim, heb_helekim, "Bach", u'ב"ח')
    parse_text(eng_helekim, files_helekim, "Bach")
    post_commentary("Bach")
  num_comments_mismatch_small.close()
  num_comments_mismatch_big.close()
  siman_file.close()
  seif_file.close()
  