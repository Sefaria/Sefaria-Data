# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys
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

def removeExtraSpaces(txt):
	while txt.find("  ") >= 0:
		txt = txt.replace("  ", " ")
	return txt


def create_index():
	pdb.set_trace()
	tractate = ""
	if len(sys.argv) == 3:
		tractate = sys.argv[1] + "_"+sys.argv[2]
	else:
		tractate = sys.argv[1]

	root=JaggedArrayNode()
	heb_masechet = get_text_plus(tractate)['heBook']
	root.add_title(u"Ramban on "+tractate.replace("_"," "), "en", primary=True)
	root.add_title(u'רמב"ן על '+heb_masechet, "he", primary=True)
	root.key = 'ramban'
	root.sectionNames = ["Daf", "Comment"]
	root.depth = 2
	root.addressTypes = ["Talmud","Integer"]

	root.validate()

	index = {
		"title": "Ramban on Bava Batra",
		"categories": ["Commentary2", "Talmud", "Ramban"],
		"schema": root.serialize()
	}
	post_index(index)
	return tractate
'''
perek = 5@.*?2@
daf = 2@.*?\d@
dh = 4@.*?1@
before_dh = 7@.*?4@ or 1@.*?4@

'''
def parse():
 prev_daf = 1

 problems = open('problems.txt','w')
 text = {}
 daf = 3
 prev_daf = 3
 dh_dict = {}
 for line in open(tractate+"_complete.txt"):
	 line = line.replace("\n", "")
	 if len(line.replace(' ',''))==0:
		 continue
	 try:
		 if line.find('5')>=0:
			 perek_info = re.findall('5@.*?\d@', line)[0]
		 else:
			 perek_info = ""
		 print perek_info
		 if line.find('2')>=0:
			 daf_info = re.findall('2@.*?\d@', line)[0]
		 else:
			 daf_info = ""
		 print daf_info
		 dh_info = re.findall('4@.*?1@', line)[0]

		 print dh_info
		 if line.find('7@')>0:
		   before_dh_info = re.findall('7@.*?4@', line)[0]
		 else:
		   poss = re.findall('1@.*?4@', line)
		   if len(poss)>0:
			 before_dh_info = poss[0]
		   else:
			 before_dh_info = ""
		 print before_dh_info
	 except:
		 problems.write(tractate+"\n"+line+"\n\n")
		 pdb.set_trace()
		 continue
	 if len(daf_info)>0:
		 daf = daf_info.replace("2@", "").replace("1@","").replace("7@","")
		 if daf.find('דף')==-1 and daf.find('ע"')==-1:
			 print 'no daf'
			 pdb.set_trace()
		 if daf.find('ע"ב')>0:
			 amud = 0
		 else:
			 amud = -1
		 daf = amud + (2*getGematria(daf.replace('ע"ב', '').replace('ע"א','').replace('דף','')))

	 dh = dh_info.replace("4@","").replace("1@","")
	 before_dh = before_dh_info.replace("7@","").replace("1@","").replace("4@","")
	 comment_start = line.rfind("1@")
	 comment = line[comment_start+2:].replace("3@","<br>")
	 comment = comment.replace(" .", ".")
	 comment = removeExtraSpaces(comment)
	 if type(daf) is int and daf not in text:
		 if daf < prev_daf:
			 print 'daf error'
			 pdb.set_trace()
		 text[daf] = []
		 dh_dict[daf] = []
		 prev_daf = daf
	 text[daf].append(before_dh + "<b>" + dh+"</b>"+comment)
	 dh_dict[daf].append(dh)
	 return text, dh_dict
def post():
 text_array = convertDictToArray(text)
 send_text = {
	 "text": text_array,
	 "versionTitle": "Ramban on Talmud",
	 "versionSource": "http://www.sefaria.org",
	 "language": "he"
 }
 post_text("Ramban on "+tractate.replace("_"," "), send_text)
 links_to_post = []
 match = Match(in_order=True, min_ratio=80, guess=False, range=True, can_expand=False)
 for daf in dh_dict:
	 dh_list = dh_dict[daf]
	 daf_array = get_text(tractate+"."+AddressTalmud.toStr("en", daf))
	 results = match.match_list(dh_list, daf_array, tractate+" "+AddressTalmud.toStr("en", daf))
	 for key, value in results.iteritems():
		 value = value.replace("0:", "")
		 talmud_end = tractate + "." + AddressTalmud.toStr("en", daf) + "." + value
		 ramban_end = "Ramban_on_" + tractate + "." + AddressTalmud.toStr("en", daf) + "." + str(key)
		 links_to_post.append({'refs': [talmud_end, ramban_end], 'type': 'commentary', 'auto': 'True', 'generated_by': "ramban"+tractate})    
 problems.close()
 post_link(links_to_post)


if __name__ == "__main__":
	global tractate
	global text
	global dh_dict
	create_index()
	parse()
	post()