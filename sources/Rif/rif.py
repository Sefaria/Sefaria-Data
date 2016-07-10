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
import glob
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




class RifTractate
{
	def __init__(self, eng_title, he_title):
		createIndex()
		self.eng_title = eng_title
		self.he_title = he_title
		

	def run(self):
		initial_text = getText(eng_title)
		processed_text, links = getAmudimAndLinks(text)
		postRif(processed_text, links)


	def createIndex(self):
		rif = JaggedArrayNode()
		rif.add_title(self.eng_title, "en", primary=True)
		rif.add_title(self.he_title, "he", primary=True)
		rif.key = self.eng_title
		rif.depth = 2
		rif.addressTypes = ["Talmud", "Integer"]
		rif.sectionNames = ["Amud", "Comment"]
		rif.validate()
	 	index = {
	    "title": self.eng_title,
	    "categories": ["Commentary2", "Talmud", "Rif"],
	    "schema": rif.serialize()
	    }
	 	post_index(index)


	def getText(self):
		text = ""
		for line in open(self.eng_title+".txt"):
			if line.find('@') == line.rfind('@') and line.find('@13')>=0:
				line = line.replace('\n', '')
			text += line.replace('@00', '').replace('@44', '<b>').replace('@55', '</b>')
		return text


	def getAmudimAndLinks(self, text):
		text = text.split("@20")
		links = {}
		for amud_count in range(len(text)):
			text[amud_count] = text[amud_count].decode('utf-8')
			text[amud_count] = text[amud_count].split('\n')
			links[amud_count] = []
			for comment_count in range(len(text[amud_count])):
				links_this_comment = []
				matches = re.findall(u'\(@13[\u05D0-\u05EA\s]+ [\u05D0-\u05EA]+ [\u05D0-\u05EA"]+\)', text[amud_count][comment_count])
				for match in matches:
					match_split_len = len(match.split(" "))
					if match_split_len == 4:
						masechet = " ".join(match.split(" ")[0:2])
						modified_match = match.replace(' ', '', 1)
						which_daf = getGematriaDaf(modified_match)
						links_this_comment.append((masechet, which_daf))
						text[amud_count][comment_count] = text[amud_count][comment_count].replace(match, "")
					elif match_split_len == 3:
						which_daf = getGematriaDaf(match)
						masechet = self.he_title if match.split(" ")[0] == u"(@13דף" else match.split(" ")[0].replace("(@13", "")
						links_this_comment.append((masechet, which_daf))
						text[amud_count][comment_count] = text[amud_count][comment_count].replace(match, "")
			links[amud_count].append(links_this_comment)
		pdb.set_trace()
		return text, links



	def postRif(self, amudim, links):
		send_text = {
			"text": amudim,
			"versionTitle": "Vilna Edition",
			"versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
			"language": "he"
		}
		post_text("Rif_Megillah", send_text)


	}

		