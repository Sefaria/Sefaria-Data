# -*- coding: utf-8 -*-
import urllib2
import urllib
from urllib2 import URLError, HTTPError
import json 
import pdb
import glob
import os
import sys
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from data_utilities import util, sanity_checks
from data_utilities.sanity_checks import TagTester

def checkPerakim():
	for file in glob.glob(u"*.txt"):
		if file.find("intro") == -1:
			print file
			reg = u'(?:@00\u05e4\u05e8\u05e7 |@00\u05e4")([\u05d0-\u05ea]+)'
			open_file = open(file)
			tt = TagTester("@00", open_file, perek_checker, reg=reg)
			tt.in_order_one_section(1)

def checkMishnayot():
	for file in glob.glob(u"*.txt"):
		if file.find("intro") == -1:
			print file
			reg = u'@22.*?[\u05d0-\u05ea]+.*?'
			open_file = open(file)
			tt = TagTester("@22", open_file, perek_checker, reg=reg)
			tt.in_order_many_sections(end_tag="@00")

def perek_checker(curr_val, prev_val):
	return (curr_val >= prev_val)

if __name__ == "__main__":
	checkPerakim()


