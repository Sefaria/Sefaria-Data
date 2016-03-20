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


'''options:
missing one is the only one: in this case, just set 0 to length
missing one is at beginning: perhaps if first match is at position greater than 7, create a new one from 0 till the first one
missing one is in middle: will get grouped into the one before it
missing one is at end: will get grouped into the one before it
'''

file = "English Rashi on Shemot.txt"
text = {}
perek = 0
for line in open(file):
	passukim = re.split('\(\d+\)', line)
	for count, pasuk in enumerate(passukim):
		if count == 0:
			digit = re.findall('@\d', pasuk)
			int(digit)
			perek = digit
			text[perek] = []
			continue
		pasuk = pasuk.replace("#", "")
		poss_matches = re.findall(u"[\u05D0-\u05EA\s]+[.,a-zA-Z0-9\[\]\s]+[A-Z][A-Z]+", pasuk)
		matches = []
		
		if len(poss_matches) == 0:
			matches.append(pasuk)
		if pasuk.find(poss_matches[0]) > 7:
			pos = pasuk.find(poss_matches[0])
			matches.append(pasuk[0:pos])

		for poss_match in poss_matches:
			match_wout_hebrew = re.sub(u"[\u05D0-\u05EA]+", "", poss_match)
			if match_wout_hebrew != poss_match:
				pos = pasuk.find(poss_match)
				matches.append(poss_match)
		
	