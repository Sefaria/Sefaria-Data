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

'''
First, take each paragraph that starts with 11, and set the daf according to the second word in the paragraph.
Convert "@22" into "@44".  When separating dicts of dh and comment, leave 'בד"ה' in comment, but in dh take it out.
Consider case when there is no first sentence/no dh.  What is בא"ד?
What does בד"ה ורבנן הוא דאצריך וכו' משום דאיכא דאשכח וכו' mean? "This and that? Until?"
Split the text into comments on "@44". For each comment, determine the category:
if it's Gemara, Rashi, Tosafot, Amud Bet, or something else.
For comm_dict[current_daf], append a tuple: (category, comment with dh bolded, dh)

How to check Rashi/Tosafot?
>>> text = get_text("Rashi on Gittin.2a.15")
>>> text['next']
u'Rashi on Gittin 2b:1'
'''

def addDHComment(dh1, dh2, comment, category):
	if len(dh1)>0 and len(dh2)>0:
		dh_dict[category][current_daf].append(dh1)
		dh_dict[category][current_daf].append(dh2)
		comm_dict[current_daf].append("<b>"+dh1+" "+dh2+" </b>"+comment)
	elif len(dh1)>0:
		dh_dict[category][current_daf].append(dh1)
		dh_dict[category][current_daf].append("")
		comm_dict[current_daf].append("<b>"+dh1+" </b>"+comment)
	else:
		last_comment = len(comm_dict[current_daf])-1
		if last_comment == -1:
			comm_dict[current_daf].append(comment)
			dh_dict[category][current_daf].append("")
			dh_dict[category][current_daf].append("")
		else:
			comm_dict[current_daf][last_comment] += "<br>"+comment
comm_dict = {}
dh_dict = {}
if len(sys.argv) == 3:
	masechet = sys.argv[1]+" "+sys.argv[2]
else:
	masechet = sys.argv[1]
rashi ='רש"י'
tosafot = "תוס"
gemara = "גמ"
amud_bet = 'ע"ב'
mishnah = 'במשנה'
other_tosafot = 'בא"ד'
current_daf = 0
categories = ['rashi', 'tosafot', 'gemara', 'mishnah', 'paragraph']
for category in categories:
	dh_dict[category] = {}
f = open(masechet+"2.txt", 'r')
for line in f:
	line = line.replace("\n", "")
	line = line.replace("@33", "@44")
	line = line.replace("@55", "")
	line = line.replace('בד"ה', '')
	if line.find("@11")>=0:
		if line.split(" ")[0].find('דף')>=0:
			daf_value = getGematria(line.split(" ")[1].replace('"', '').replace("'", ''))
			if line.split(" ")[2].find(amud_bet)>=0:
				current_daf = 2*daf_value
			else:
				current_daf = 2*daf_value - 1
			actual_text = ""
			for count, word in enumerate(line.split(" ")):
				if count >= 3:
					actual_text += word + " "
		else:
			current_daf += 1
			actual_text = line[4:]
			
		if not current_daf in comm_dict:
			comm_dict[current_daf] = []
				
			
			 
		comments = actual_text.split("@44")
		for comment in comments:
			if comment == comments[0] and len(comment) == 0:
				continue
			category = comment.split(" ")[0]
			if category.find(rashi)>=0:
				category = 'rashi'
			elif category.find(other_tosafot)>=0:
				category = 'tosafot'
			elif category.find(tosafot)>=0:
				category = 'tosafot'
			elif category.find(gemara)>=0:
				category = 'gemara'
			elif category.find(mishnah)>=0:
				category = 'mishnah'
			else:
				category = 'paragraph'
			
			if not current_daf in dh_dict[category]:
				dh_dict[category][current_daf] = []
			
			if category == 'paragraph':
				addDHComment("","", comment, 'paragraph')
			else:
				end_of_first_word = comment.find(' ')
				comment = comment[end_of_first_word+1:]
				marker_max = max(comment.rfind('.'), comment.rfind(':'))
				marker_min = min(comment.find('.'), comment.find(':'))
				if marker_min == -1:
					marker_min = max(comment.find('.'), comment.find(':'))
				if marker_min == marker_max or (onlyOne(comment, '.') and onlyOne(comment, ':') and comment.find('.')>comment.find(':')):
					print comment
					if onlyOne(comment, "כו'"):
						dh1, comment = comment.split("כו'", 1)
						if len(comment)<5:
							dh1 += "כו'"
						else:
							dh1 += "כו'. "
						dh2 = ""
					elif comment.find("כו'")>=0: #multiple cases	
						dh1, dh2, comment = comment.split("כו'", 2)	
						dh1 += "כו' "
						if len(comment)<5:
							dh2 += "כו'"
						else:
							dh2 += "כו'. "			
					else: #no periods or etc so nothing to work with, should this be a comment or DH?
							#depends on whether it's paragraph comment??
						dh1 = ""
						dh2 = ""	
				elif comment.find(".")>=0:
					dh, comment = comment.split(".", 1)
					dh += ". "
					if onlyOne(dh, "כו'"):  
						dh1 = dh
						dh2 = ""
					elif dh.find("כו'")>=0:
						dh1, dh2 = dh.split("כו'", 1)
						dh1 += "כו' "	
					else:
						dh1 = dh
						dh2 = ""
				addDHComment(dh1, dh2, comment, category)
	else:
		print 'line did not start with 11'

match_obj=Match(in_order=False, min_ratio=80, guess=False, range=False)

last_daf = max(comm_dict.keys())
param = "off"
for daf in comm_dict:
	if daf==last_daf:
		param = "on"
	send_text = {
				"versionTitle": "Maharam Shif on "+masechet,
				"versionSource": "http://www.sefaria.org",
				"language": "he",
				"text": comm_dict[daf],
				}
	post_text("Maharam Shif on "+masechet+"."+AddressTalmud.toStr("en", daf), send_text, param)


for category in categories:
  if category=='paragraph':
  	continue
  elif category=='gemara':
  	title = masechet
  elif category=='rashi':
  	title = "Rashi on "+masechet
  elif category=='tosafot':
  	title = "Tosafot on "+masechet
  	
  for daf in dh_dict[category]:
  	dh_arr = dh_dict[category][daf]
  	text = compileCommentaryIntoPage(title, daf)
	result = match_obj.match_list(dh_arr, text, title+" "+AddressTalmud.toStr("en", daf))
	for key in result:
		if result[key][0] != 0 and key % 2 == 1:
			masechet_daf_line_start = lookForLineInCommentary(title, daf, result[key][0])
			masechet_daf_line_end = lookForLineInCommentary(title, daf, result[key][1])
			#need to check if the range could be valid, not if end is greater than start
				masechet_daf_line = Ref(masechet_daf_line_start).to(Ref(masechet
			else:
				masechet_daf_line = masechet_daf_line_start
			post_link({
				"refs": [
						 masechet_daf_line,
						"Maharam Shif on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(key)
					],
				"type": "commentary",
				"auto": True,
				"generated_by": "Maharam Shif on "+masechet+" linker",
			 })
		'''what needs to be done?  check all dh1s as normal in order and attempt to add in dh2 ranges later.
		but what about the text itself?  write function to go through all comments appending each one to an array
		(as in two per line, two get added to array), this entire chunk is the daf sent to matching algorithm.
		then afterward, for each dh1 and its matched line, start at 2a.1, for loop on 2a.1['he'], each iteration 
		incrementing the count, when for loop is done, reset to 2a.1['next'] unless ['next'] is 2b.
		then still, this only matches dh1s.  what about dh2s?  
		MAJOR PROBLEM: the dhs are to different texts....there should be a different dictionary per text
		what about out of order passing each dh1 and dh2 even blank ones as we know blank gets matched to 0
		
		'''