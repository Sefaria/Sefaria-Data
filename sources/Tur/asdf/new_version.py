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
sys.path.insert(0, '../../Match/')
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
 
def create_indexes(helekim, files, eng_title, heb_title):
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
  #post_index(index)
	
def checkCSV(helek, commentator, siman, num_comments):
	print 'hi'
	'''
	csvf = open('comments_per_siman.csv', 'r')
	csvreader = csv.reader(csvf, delimiter=',')
	csvreader = csv.reader(csvf, delimiter=',')
	for row in csvreader:
		if helek == row[0] and commentator == row[1] and str(siman) == row[2]:
			if str(num_comments) != row[3]:
				num_comments_mismatch.write(helek+","+commentator+","+str(siman)+","+str(num_comments)+","+row[3])
				print 'inconsistent'
			else:
				print 'consistent'
	csvf.close()
	'''
def dealWithTwoSimanim(text):
	if text[0] == ' ':
		text = text[1:]
	if text[len(text)-1] == ' ':
		text = text[:-1]
	if len(text.split(" "))>1:
		if len(text.split(" ")[0]) > 0 and len(text.split(" ")[1]) > 0:
			text = text.split(" ")[0]
	return text

def parse_text(helekim, files, commentator):
  store_this_line = ""
  for count, helek in enumerate(helekim):
    curr_siman = 0
    curr_seif_katan = 0
    f = open(files[count])
    text[helek] = {}
    seif_list = []
    for line in f:
  	  print helek+"<br>"+line
  	  actual_line = line
  	  line = line.replace("סימן", "סי")
  	  line = line.replace("\n", "")
  	  first_word = line.split(" ")[0]
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
		  if poss_siman <= curr_siman:
		  		print 'siman issue'
		  		siman_file.write(helek+","+commentator+",_New_Siman:_"+str(poss_siman)+",_Previous Siman:_"+str(curr_siman)+",_Beginning_of_Line: "+first_word+"\n")		  				
		  if curr_siman > 0:
				checkCSV(helek, commentator, curr_siman, len(text[helek][curr_siman]))
		  curr_siman = poss_siman
		  curr_seif_katan = 0
		  text[helek][curr_siman] = {}
		  seif_list = []
		  line = "@"+line
	  if (line.find("@66@22")>=0 or line.find("@77@22")>=0) and len(line.split(" "))>4:  #ONLY BEIT YOSEF and BACH ON YOREH DEAH
		  beg, line = line.split(" ", 1)
		  beg = beg.replace("@66@22","")
		  beg = dealWithTwoSimanim(beg)
		  poss_siman = getGematria(beg)
		  if poss_siman <= curr_siman:
		  		print 'siman issue'
		  		siman_file.write(helek+","+commentator+",_New_Siman:_"+str(poss_siman)+",_Previous Siman:_"+str(curr_siman)+",_Beginning_of_Line: "+first_word+"\n")		  				
		  if curr_siman > 0:
				checkCSV(helek, commentator, curr_siman, len(text[helek][curr_siman]))
		  curr_siman = poss_siman
		  curr_seif_katan = 1
		  text[helek][curr_siman] = {}
		  seif_list = []
		  seif_list.append(curr_seif_katan)
		  text[helek][curr_siman][curr_seif_katan] = [line]
	  #now process three typical cases: Siman header, Comment with Seif Katan marker, Comment without Seif Katan marker	
	  if pattern.match(line):
		seif_katan = pattern.match(line).group(0)
		temp_arr = re.split('\d\d', seif_katan)
		seif_katan = temp_arr[len(temp_arr)-1]
		poss_seif_katan = getGematria(removeAllStrings(["[","]","(",")"], seif_katan))
		if poss_seif_katan < curr_seif_katan and (curr_siman != 24 and curr_siman != 33):
			seif_file.write(helek+","+commentator+",_New_Seif_Katan:_"+str(poss_seif_katan)+",_Previous_Seif_Katan:_"+str(curr_seif_katan)+",_Beginning_of_Line:_"+first_word+"\n")
			
		if poss_seif_katan in seif_list:
			seif_katan = pattern.match(line).group(0)
			marked_seif_katan = seif_katan[0:len(seif_katan)-1]+'*'+seif_katan[len(seif_katan)-1]
			line = line.replace(seif_katan, marked_seif_katan)
		else:
			seif_katan = pattern.match(line).group(0)
			line = line.replace(seif_katan, "")
			seif_list.append(poss_seif_katan)
			
	#	elif poss_seif_katan < curr_seif_katan and (curr_siman != 24 and curr_siman != 33):
	#		seif_file.write(helek+","+commentator+","+str(curr_siman)+","+str(poss_seif_katan)+","+str(curr_seif_katan)+","+actual_line+"\n")
	#		print 'seif katan'
		line = removeAllStrings(["@11", "@22","@33", "@44", "@55", "@66", "@77", "@87","@88","@89", "@98"], line)
		if curr_seif_katan == poss_seif_katan:
			text[helek][curr_siman][curr_seif_katan][0] += "<br>"+line
		else:
			curr_seif_katan = poss_seif_katan
			curr_seif_katan_line = actual_line
			if line.find("@")>=0:
				print '@'
				pdb.set_trace()
			text[helek][curr_siman][curr_seif_katan] = [line]			
	  elif line.find("@22סי'")>=0 or (line.find("@22")<6 and line.find("@22")>=0 and len(line.split(" ")) < 4):
			line = line.replace("@22סי' ", "").replace("@22ס' ","").replace("@22סי ","")
			line = line.replace("@22", "").replace("@66","").replace("@77","")
			if curr_siman > 0:
				checkCSV(helek, commentator, curr_siman, len(text[helek][curr_siman]))
			if len(line) > 0:
				line = dealWithTwoSimanim(line)
				poss_siman = getGematria(line)
			else:
				poss_siman += 1
	  		if poss_siman <= curr_siman:
		  		print 'siman issue'
		  		siman_file.write(helek+","+commentator+",_New_Siman:_"+str(poss_siman)+",_Previous Siman:_"+str(curr_siman)+",_Beginning_of_Line: "+first_word+"\n")		  				
			prev_siman = curr_siman
			curr_siman = poss_siman
			curr_seif_katan = 0
			seif_list = []
			text[helek][curr_siman] = {}
	  else: #just add it to current seif katan
	  	print line
		line = removeAllStrings(["@", "1", "2", "3", "4", "5", "6", "7", "8", "9"], line)
		if line.find("@")>=0:
			print line.find("@")
			pdb.set_trace()
		if commentator == "Prisha" or commentator == "Drisha" or helek == "Choshen Mishpat":
			if len(text[helek][curr_siman]) == 0:
				text[helek][curr_siman][curr_seif_katan] = [""]
			text[helek][curr_siman][curr_seif_katan][0] += "<br>"+line
		else:
			curr_seif_katan += 1
			text[helek][curr_siman][curr_seif_katan] = [line]
	  prev_line = actual_line
	  


if __name__ == "__main__":
  import csv
  global siman_file
  global seif_file    
  siman_file = open('siman_probs.csv', 'a')
  seif_file = open('seif_probs.csv', 'a')
  num_comments_mismatch = open('num_comments_mismatch.csv', 'w')
  eng_helekim = ["Yoreh_Deah", "Choshen_Mishpat", "Even_HaEzer", "Orach_Chaim"]
  heb_helekim = [u"יורה דעה", u"חושן משפט", u"אבן העזר", u"אורח חיים"]
  if sys.argv[1] == 'Drisha':
  	files_helekim = ["yoreh deah/drisha.txt", "choshen mishpat/drisha.txt",
   "even haezer/drisha.txt", "orach chaim/drisha.txt"]
  	create_indexes(eng_helekim, heb_helekim, "Drisha", u"דרישה")
  	parse_text(eng_helekim, files_helekim, "Drisha")
  elif sys.argv[1] == 'Prisha':
  	files_helekim = ["yoreh deah/prisha.txt", "choshen mishpat/prisha.txt",
   "even haezer/prisha.txt", "orach chaim/prisha.txt"]
  	create_indexes(eng_helekim, heb_helekim, "Prisha", u"פרישה")
  	parse_text(eng_helekim, files_helekim, "Prisha")
  elif sys.argv[1].find('Bi')>=0:
  	files_helekim =  ["yoreh deah/bi.txt", "choshen mishpat/bi.txt",
   "even haezer/bi.txt", "orach chaim/bi.txt"]
  	create_indexes(eng_helekim, heb_helekim, "Bi", u'ב"י')
  	parse_text(eng_helekim, files_helekim, "Bi")
  elif sys.argv[1].find("Bach")>=0:
    files_helekim =  ["yoreh deah/bach.txt", "choshen mishpat/bach.txt",
   "even haezer/bach.txt", "orach chaim/bach.txt"]
    create_indexes(eng_helekim, heb_helekim, "Bach", u'ב"ח')
    parse_text(eng_helekim, files_helekim, "Bach")
  num_comments_mismatch.close()
  siman_file.close()
  seif_file.close()
  