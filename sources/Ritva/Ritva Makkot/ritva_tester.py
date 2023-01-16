# -*- coding: utf-8 -*-
import urllib2
import urllib
from urllib2 import URLError, HTTPError
import json 
import pdb
import glob
import os
import sys
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from data_utilities import util, sanity_checks
from parsing_utilities.sanity_checks import TagTester
from functions import *
from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *


def perek_checker(prev_val, curr_val):
	return (curr_val > prev_val)

def checkPerakim():
	files = ["Yoma"]
	for file in files:
		print file
		reg = u'(?:@00\u05e4\u05e8\u05e7 |@00\u05e4")([\u05d0-\u05ea]+)'
		open_file = open(file)
		tt = TagTester("@00", open_file, reg=reg)
		tt.in_order_one_section(1, perek_checker)

def checkDappim():
	file = open()
	#check that we go in order, redo above test
	#check that nothing is missing, redo above test except that we dont want it to fail 
	#separate function print the dappim headers into a file