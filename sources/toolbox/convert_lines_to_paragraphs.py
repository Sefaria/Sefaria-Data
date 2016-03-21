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
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *
import argparse
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud
import pdb


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--input", help="Name of input file.")
	parser.add_argument("--output", help="Name of output file.")
	parser.add_argument("--end_tag", help="Tag that indicates the end of a comment.")
	args = parser.parse_args()
	input_file = args.input
	output_file = args.output
	end_tag = args.end_tag
	comment = ""
	out = open(output_file, 'w')
	for line in open(input_file):
		line = line.replace('\r', '')
		line = line.replace("\n","")
		if line.find(end_tag) == -1:
			comment+=line
		else:
			comment+=line.replace(end_tag,"")
			out.write(comment+'\n')	
			comment = ""
	if len(comment) > 0:
		out.write(comment+'\n')