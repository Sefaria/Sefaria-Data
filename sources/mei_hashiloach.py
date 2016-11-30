# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import sys
import re
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)

os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud




def replaceBadNodeTitles(title, bad_char, good_char):
	def recurse(node):
		if 'nodes' in node:
			for each_one in node['nodes']:
				recurse(each_one)
		elif 'default' not in node:
			node['title'] = node['title'].replace(bad_char, good_char)
			if node['titles'][0]['lang']
			node['titles'][0]['text'] = node['titles'][0]['text'].replace(bad_char, good_char)

	data = library.get_index(title).nodes.serialize()
	recurse(data)
	return data




if __name__ == "__main__":
	title = "Mei_HaShiloach"
	replaceBadNodeTitlesHelper(title, replaceBadNodeTitles, "Vaysihlach", "Vayishlach")
	



