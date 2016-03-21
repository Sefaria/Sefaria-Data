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
pattern =  re.compile('(@\d\d)+[\[\(][^&]{1,4}[\]\)]')
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
	for row in csvreader:
		if helek == row[0] and commentator == row[1] and str(siman) == row[2]:
			if str(num_comments) != row[3]:
				print 'inconsistentcy '+str(num_comments)+' vs '+row[3]
				pdb.set_trace()
			else:
				print 'consistent'

def parse_text(helekim, files, commentator):
  store_this_line = ""
  for count, helek in enumerate(helekim):
    curr_siman = 0
    curr_seif_katan = 0
    f = open(files[count])
    text[helek] = {}
    for line in f:
  	  actual_line = line
  	  line = line.replace("\n", "")
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
	  if pattern.match(line):
		seif_katan = pattern.match(line).group(0)
		temp_arr = re.split('\d\d', seif_katan)
		seif_katan = temp_arr[len(temp_arr)-1]
		poss_seif_katan = getGematria(removeAllStrings(["[","]","(",")"], seif_katan))
		if poss_seif_katan < curr_seif_katan:
			print 'seif katan'
			pdb.set_trace()
		curr_seif_katan = poss_seif_katan
		if curr_seif_katan == 7 and helek == "Choshen Mishpat" and curr_siman == 65:
			pdb.set_trace()
		first_space = line.find(' ')
		line = line[first_space+1:]
		line = removeAllStrings(["@11", "@22","@33", "@44", "@55", "@66", "@77", "@88","@89", "@98"], line)
		if line.find("@")>=0:
			print '@'
			pdb.set_trace()
		text[helek][curr_siman][curr_seif_katan] = [line]
	  elif line.find("@66@22")>=0 and len(line)>17:  #ONLY BEIT YOSEF ON YOREH DEAH
		  beg, line = line.split(" ", 1)
		  beg = beg.replace("@66@22","")
		  poss_siman = getGematria(beg)
		  if poss_siman < curr_siman:
		  		print 'siman issue'
				pdb.set_trace()
		  if curr_siman > 0:
		  		pdb.set_trace()
				checkCSV(helek, commentator, curr_siman, len(text[helek][curr_siman]))
		  curr_siman = poss_siman
		  text[helek][curr_siman] = [line]
	  elif line.find("@22סי'")>=0 or (line.find("@22")<4 and line.find("@22")>=0):
		line = line.replace("@22סי' ", "").replace("@22ס' ","").replace("@22סי ","")
		line = line.replace("@22", "").replace("@66","")
		poss_siman = getGematria(line)
		if poss_siman < curr_siman:
			print 'siman issue'
			pdb.set_trace()
		#check if curr_siman's comments are same as in file
		if curr_siman > 0:
			print curr_siman > 0
			print curr_siman
			checkCSV(helek, commentator, curr_siman, len(text[helek][curr_siman]))
		curr_siman = poss_siman
		if helek != "Choshen Mishpat" and (commentator == "Bach" or commentator == "Bi"):
			text[helek][curr_siman] = [""]
		else:
			text[helek][curr_siman] = {}
		curr_seif_katan = 0
	  elif line.find("@00")>=0:
	  	continue
	  else: #just add it to current seif katan
	  	#print line
		line = removeAllStrings(["@", "1", "2", "3", "4", "5", "6", "7", "8", "9"], line)
		if line.find("@")>=0:
			print line.find("@")
			pdb.set_trace()
		if helek != "Choshen Mishpat" and (commentator == "Bach" or commentator == "Bi"):
			text[helek][curr_siman][0] = text[helek][curr_siman][0]+"<br>"+line
		else:
			text[helek][curr_siman][curr_seif_katan][0] = text[helek][curr_siman][curr_seif_katan][0]+"<br>"+line



if __name__ == "__main__":
  import csv
  csvf = open('comments_per_siman.csv', 'r')
  global csvreader
  csvreader = csv.reader(csvf, delimiter=',')
  eng_helekim = ["Yoreh Deah", "Choshen Mishpat", "Even HaEzer", "Orach Chaim"]
  heb_helekim = [u"יורה דעה", u"חושן משפט", u"אבן העזר", u"אורח חיים"]
  if sys.argv[1] == 'Drisha':
  	files_helekim = ["yoreh deah/drisha yoreh deah.txt", "Choshen Mishpat/prisha choshen mishpat.txt",
   "Even HaEzer/drisha even haezer.txt", "OrachChaim/drisha orach chaim helek a.txt"]
  	create_indexes(eng_helekim, heb_helekim, "Drisha", u"דרישה")
  	parse_text(eng_helekim, files_helekim, "Drisha")
  elif sys.argv[1] == 'Prisha':
  	files_helekim = ["yoreh deah/prisha yoreh deah.txt", "Choshen Mishpat/prisha choshen mishpat.txt",
   "Even HaEzer/prisha even haezer.txt", "OrachChaim/prisha orach chaim helek a.txt"]
  	create_indexes(eng_helekim, heb_helekim, "Prisha", u"פרישה")
  	parse_text(eng_helekim, files_helekim, "Prisha")
  elif sys.argv[1] == 'Bi':
  	files_helekim = ["yoreh deah/beit yosef yoreh deah.txt", "Choshen Mishpat/Bi choshen mishpat.txt","Even HaEzer/Bi Even HaEzer.txt", "OrachChaim/beit yosef orach chaim helek a.txt"]
  	create_indexes(eng_helekim, heb_helekim, "Bi", u'ב"י')
  	parse_text(eng_helekim, files_helekim, "Bi")
  elif sys.argv[1] == "Bach":
    files_helekim = ["yoreh deah/bach yoreh deah.txt", "Choshen Mishpat/bach choshen mishpat.txt","Even HaEzer/bach even haezer.txt", "OrachChaim/bach orach chaim helek a.txt"]
    create_indexes(eng_helekim, heb_helekim, "Bach", u'ב"ח')
    parse_text(eng_helekim, files_helekim, "Bach")
  