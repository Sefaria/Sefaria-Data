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

if len(sys.argv) == 3:
	masechet = sys.argv[1]+" "+sys.argv[2]
else:
	masechet = sys.argv[1]

heb_numbers = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "ששי", "שביעי", "שמיני", "תשיעי", "עשירי", "אחד עשר", "שנים עשר", "שלשה עשר"] 


def convertRefCommentaryTalmud(ref, replace_text):
	ref = ref.replace('.', ':')
	if ref.find('-')==-1:
		first_case = True
	else:
		which_range = ref.split('-')[1].find(':')
		if which_range == -1:
			first_case = True
			ref = ref.split('-')[0]
		else:
			refs = []
			beg, end = ref.split('-')
			refs.append(beg)
			refs.append(end)
			first_colon = beg.find(':')
			second_colon = beg.rfind(':')
			if second_colon <= first_colon: 
				pdb.set_trace()
			beg = beg[0:second_colon]	
			only_colon = end.find(':')
			if only_colon == -1:
				pdb.set_trace()
			end = end[0:only_colon]
			return beg.replace(replace_text,"")+'-'+end
	if first_case:
		first_colon = ref.find(':')
		second_colon = ref.rfind(':')
		if second_colon <= first_colon: 
			pdb.set_trace()
		ref = ref[0:second_colon]		
	return ref.replace(replace_text, "")
		
def addDHComment(dh1, dh2, comment, category, heb_category):
	if hasTags(dh1) or hasTags(dh2) or hasTags(comment):
		print "tags!"
		pdb.set_trace()
	if len(dh1)>0 and len(dh2)>0:
		dh1_dict[current_daf].append((category, dh1))
		dh2_dict[current_daf].append((category, dh2))
		comm_dict[current_daf].append(heb_category+" <b>"+dh1+" "+dh2+" </b>"+comment)
	elif len(dh1)>0:
		dh1_dict[current_daf].append((category, dh1))
		dh2_dict[current_daf].append((category, ""))
		comm_dict[current_daf].append(heb_category+" <b>"+dh1+" </b>"+comment)
	else:
		last_comment = len(comm_dict[current_daf])-1
		if last_comment == -1:
			comm_dict[current_daf].append(comment)
			dh1_dict[current_daf].append((category, ""))
			dh2_dict[current_daf].append((category, ""))
		else:
			if comment.find("""בד"ה ומר סבר כו' ומאן""")>=0:
				pdb.set_trace()
			comm_dict[current_daf][last_comment] += "<br>"+comment		
	if category == 'gemara':
		gemara1_dict[current_daf].append(dh1)
		gemara2_dict[current_daf].append(dh2)
	elif category == 'rashi':
		rashi1_dict[current_daf].append(dh1)
		rashi2_dict[current_daf].append(dh2)
	elif category == 'tosafot':
		tosafot1_dict[current_daf].append(dh1)
		tosafot2_dict[current_daf].append(dh2)
	elif category == 'mishnah':
		mishnah1_dict[current_perek].append(dh1)
		mishnah2_dict[current_perek].append(dh2)
	
def removeBDH(array):
	try:
		new_array = []
		for elem in array:
			elem = elem.replace('בד"ה', '')	
			new_array.append(elem)
	except:
		pdb.set_trace()
	return new_array
	
comm_dict = {}
dh1_dict = {}
dh2_dict = {}
gemara1_dict = {}
gemara2_dict = {}
tosafot1_dict = {}
tosafot2_dict = {}
rashi1_dict = {}
rashi2_dict = {}
mishnah1_dict = {}
mishnah2_dict = {}
rashi ='רש"י'
tosafot = "תוס"
dibbur_hamatchil = 'בד"ה'
dibbur_hamatchil_2 = 'ד"ה'
gemara = "גמ"
amud_bet = 'ע"ב'
mishnah = 'במשנה'
other_tosafot = 'בא"ד'
current_daf = 3
current_perek = 1
categories = ['rashi', 'tosafot', 'gemara', 'mishnah', 'paragraph']
f = open(masechet+"2.txt", 'r')
this_line = False
for line in f:
	line = line.replace("\n", "")
	line = line.replace("@33", "@44")
	line = line.replace("@55", "")
	line = line.replace("@77","").replace("@99","")
	if len(line)==0:
		continue
	if line.find("@00")>=0 and line.find("פרק")>=0:
		which_perek = -1
		for count, word in enumerate(heb_numbers):
			if line.find(word)>=0:
				which_perek = count+1
				break
		if which_perek == -1:
			pdb.set_trace()
		current_perek = which_perek
		continue
	if line[0] == " ":
		start = line.find("@11")
		line = line[start:]
	if line.find("@11")>=0:
		category = ""
		line = line.replace("@11 ", "@11")
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
			actual_text = line[3:]
			
		if not current_daf in comm_dict:
			comm_dict[current_daf] = []
		
		comments = actual_text.split("@44")
		for count, comment in enumerate(comments):
			if count == 0 and len(comment) == 0:
				continue
			heb_category = comment.split(" ")[0]
			if heb_category.find(rashi)>=0:
				category = 'rashi'
			elif heb_category.find(other_tosafot)>=0:
				category = 'tosafot'
			elif heb_category.find(tosafot)>=0:
				category = 'tosafot'
			elif heb_category.find(gemara)>=0:
				category = 'gemara'
			elif heb_category.find(mishnah)>=0:
				category = 'mishnah'
			elif heb_category.find(dibbur_hamatchil)>=0 or heb_category.find(dibbur_hamatchil_2)>=0:
				print 'found one'
			else:
				if count == 0:
					category = 'gemara'
				else:
					category = 'paragraph'
			if not current_daf in dh1_dict:
				dh1_dict[current_daf] = []
				dh2_dict[current_daf] = []
				gemara1_dict[current_daf] = []
				gemara2_dict[current_daf] = []
				tosafot1_dict[current_daf] = []
				tosafot2_dict[current_daf] = []
				rashi1_dict[current_daf] = []
				rashi2_dict[current_daf] = []
				mishnah1_dict[current_perek] = []
				mishnah2_dict[current_perek] = []
			if hasTags(comment):
				pdb.set_trace()
			if category == 'paragraph':
				addDHComment("","", comment, 'paragraph', "")
			else:
				end_of_first_word = comment.find(' ')
				comment = comment[end_of_first_word+1:]
				marker_max = max(comment.rfind('.'), comment.rfind(':'))
				marker_min = min(comment.find('.'), comment.find(':'))
				if marker_min == -1:
					marker_min = max(comment.find('.'), comment.find(':'))
				if marker_min == marker_max or (onlyOne(comment, '.') and onlyOne(comment, ':') and comment.find('.')>comment.find(':')):
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
						dh1 = comment
						dh2 = ""	
						comment = ""
				elif comment.find(".")>=0:
					dh, comment = comment.split(".", 1)
					dh += ". "
					if dh.find("כו'")>=0:
						dh1, dh2 = dh.split("כו'", 1)
						dh1 += "כו' "	
					else:
						dh1 = dh
						dh2 = ""
				addDHComment(dh1, dh2, comment, category, heb_category)
	else:
		print line
	prev_line = line
match_in_order=Match(in_order=True, min_ratio=80, guess=False, range=True, can_expand=False)
match_out_of_order = Match(in_order=False, min_ratio=85, guess=False, range=True, can_expand=False)
last_daf = max(comm_dict.keys())
print "HERE"
text_to_post = convertDictToArray(comm_dict)
send_text = {
				"versionTitle": "Vilna Edition",
				"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637",
				"language": "he",
				"text": text_to_post,
			}
#post_text("Maharam on "+masechet, send_text, "on")
print "HERE"

'''

dictionary for each category allows matching to work
then after we have match dictionaries for in order and out of order for each category
we go through the actual dh1_dict and dh2_dict, checking its category
whatever the category is we increment the maharam line and post the link between maharam and the appropriate
book based on the category. remember to deal with paragraph case and gemara case.
'''

mishnah_in_order = {}
mishnah_out_order = {}
for perek in mishnah1_dict:
	print "matching mishnah"
	mishnah_text = get_text_plus("Mishnah "+masechet+"."+str(perek))['he']
	mishnah_in_order[perek] = match_in_order.match_list(removeBDH(mishnah1_dict[perek]), mishnah_text, "Mishnah "+masechet+"."+str(perek))
	#mishnah_out_order[perek] = match_out_of_order.match_list(removeBDH(mishnah2_dict[perek]), mishnah_text, "Mishnah "+masechet+"."+str(perek))

links_to_post = []
for daf in dh1_dict:
	if daf < 46:
		continue
	print daf
  	maharam_line = 0
  	rashi_line=0
  	tosafot_line = 0
  	gemara_line = 0
  	mishnah_line = 0
  	tosafot1_arr = tosafot1_dict[daf]
  	tosafot2_arr = tosafot2_dict[daf]
  	rashi1_arr = rashi1_dict[daf]
  	rashi2_arr = rashi2_dict[daf]
  	gemara1_arr = gemara1_dict[daf]
  	gemara2_arr = gemara2_dict[daf]
  	print "matching tosafot"+str(len(tosafot1_arr))
  	tosafot_text = compileCommentaryIntoPage("Tosafot on "+masechet, daf)
	tosafot_in_order = match_in_order.match_list(removeBDH(tosafot1_arr), tosafot_text, "Tosafot on "+masechet+" "+AddressTalmud.toStr("en", daf))
	#tosafot_out_order = match_out_of_order.match_list(removeBDH(tosafot2_arr), tosafot_text, "Tosafot on "+masechet+" "+AddressTalmud.toStr("en", daf))
  	if not (masechet == "Bava Batra" and daf > 57):
		print "matching rashi"+str(len(rashi1_arr))
		rashi_text = compileCommentaryIntoPage("Rashi on "+masechet, daf)
		rashi_in_order = match_in_order.match_list(removeBDH(rashi1_arr), rashi_text, "Rashi on "+masechet+" "+AddressTalmud.toStr("en", daf))
		#rashi_out_order = match_out_of_order.match_list(removeBDH(rashi2_arr), rashi_text, "Rashi on "+masechet+" "+AddressTalmud.toStr("en", daf))
  	print "matching gemara"+str(len(gemara1_arr))
  	gemara_text = get_text(masechet+" "+AddressTalmud.toStr("en", daf))
	gemara_in_order = match_in_order.match_list(removeBDH(gemara1_arr), gemara_text, masechet+" "+AddressTalmud.toStr("en", daf))
	#gemara_out_order = match_out_of_order.match_list(removeBDH(gemara2_arr), gemara_text, masechet+" "+AddressTalmud.toStr("en", daf))
	dh1_arr = dh1_dict[daf]
	print "done matching"
	for category, dh in dh1_dict[daf]:
		print category
		if category == 'rashi':
			maharam_line+=1
			rashi_line+=1
			title = 'Rashi on '+masechet
			if rashi_in_order[rashi_line].find('-')>=0:
				in_order, out_order = rashi_in_order[rashi_line].split('-')
			else:
				in_order = rashi_in_order[rashi_line]
				out_order = in_order
			replace_text = "Rashi on "
		elif category == 'tosafot':
			maharam_line+=1
			tosafot_line+=1
			title = 'Tosafot on '+masechet
			if tosafot_in_order[tosafot_line].find('-')>=0:
				print tosafot_in_order[tosafot_line]
				in_order, out_order = tosafot_in_order[tosafot_line].split('-')
			else:
				in_order = tosafot_in_order[tosafot_line]
				out_order = in_order
			replace_text = "Tosafot on "
		if category == 'rashi' or category == 'tosafot':
			in_order = in_order.replace('0:','')
			out_order = out_order.replace('0:','')
			in_order = int(in_order)
			out_order = int(out_order)
			if out_order != 0: #out_order only equals 0 if there really is no Tosafot or Rashi on the given daf
				print 'hi'
				masechet_daf_line_start = lookForLineInCommentary(title, daf, in_order)
				print 'hi'
				masechet_daf_line_end = lookForLineInCommentary(title, daf, out_order)
				try:
					masechet_daf_line = Ref(masechet_daf_line_start).to(Ref(masechet_daf_line_end)).normal()
				except:
					masechet_daf_line = masechet_daf_line_start
				if len(masechet_daf_line)>0:
					post_link({
					"refs": [
								 masechet_daf_line,
								"Maharam on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(maharam_line)
							],
					"type": "commentary",
					"auto": True,
					"generated_by": "Maharam on "+masechet+" linker"})
				if len(masechet_daf_line)>0:
					talmud_ref = convertRefCommentaryTalmud(masechet_daf_line, replace_text)
					post_link({
						"refs": [
								 talmud_ref,
								"Maharam on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(maharam_line)
							],
						"type": "commentary",
						"auto": True,
						"generated_by": "Maharam "+masechet+" linker"})
		elif category == 'gemara':
			maharam_line+=1
			gemara_line+=1
			gemara_in_order[gemara_line] = gemara_in_order[gemara_line].replace('0:','')
			if gemara_in_order[gemara_line].find('-')>=0:
				in_order, out_order = gemara_in_order[gemara_line].split('-')
			else:
				in_order = gemara_in_order[gemara_line]
				out_order = in_order
			masechet_daf_line_start = masechet+" "+AddressTalmud.toStr("en", daf)+":"+in_order
			masechet_daf_line_end = masechet+" "+AddressTalmud.toStr("en", daf)+":"+out_order
			try:
				masechet_daf_line = Ref(masechet_daf_line_start).to(Ref(masechet_daf_line_end)).normal()
			except:
				masechet_daf_line = masechet_daf_line_start
			post_link({
				"refs": [
						 masechet_daf_line,
						"Maharam on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(maharam_line)
					],
				"type": "commentary",
				"auto": True,
				"generated_by": "Maharam on "+masechet+" linker",
			 })
		elif category == "mishnah":
			maharam_line+=1
			mishnah_line+=1
			pos = 0
			for perek in mishnah1_dict:
				for key in mishnah_in_order[perek]:
					pos+=1
					if pos==mishnah_line:
						mishnah_in_order[perek][key] = mishnah_in_order[perek][key].replace('0:','')
						if mishnah_in_order[perek][key].find('-')>=0:
							in_order, out_order = mishnah_in_order[perek][key].split('-')
						else:
							in_order = mishnah_in_order[perek][key]
							out_order = in_order
						in_order = int(in_order)
						out_order = int(out_order)
						masechet_daf_line_start = "Mishnah "+masechet+"."+str(perek)+"."+str(mishnah_in_order[perek][key][0])
						masechet_daf_line_end = "Mishnah "+masechet+"."+str(perek)+"."+str(mishnah_out_order[perek][key][0])
						try:
							masechet_daf_line = Ref(masechet_daf_line_start).to(Ref(masechet_daf_line_end)).normal()
						except:
							masechet_daf_line = masechet_daf_line_start
						post_link({
							"refs": [
									 masechet_daf_line,
									"Maharam "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(maharam_line)
								],
							"type": "commentary",
							"auto": True,
							"generated_by": "Maharam on "+masechet+" linker",
						})	
			
		elif category == 'paragraph' and maharam_line == 0:
			maharam_line+=1