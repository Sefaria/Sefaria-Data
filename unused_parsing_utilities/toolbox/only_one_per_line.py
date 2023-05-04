# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
from urllib.error import URLError, HTTPError
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
	parser.add_argument("--input", help="Name of input file needing to be checked.")
	parser.add_argument("--output", help="Name of output file with the results of the test.")
	parser.add_argument("--tags", help="Tags separated by separator that can only happen one time per line.")
	parser.add_argument("--separator", help="The tag separator that defaults to ;", default=";")
	args = parser.parse_args()
	input_file = args.input
	output_file = args.output
	tags = (args.tags).split(';')
	comment = ""
	out = open(output_file, 'w')
	for line in open(input_file):
		line = line.replace('\r', '')
		line = line.replace("\n","")
		for tag in tags:
			if line.find(tag) != line.rfind(tag):
				first_words = " ".join(line.split(" ")[0:4])
				print("found one")
				out.write("More than one of "+tag+" in line starting with the words: "+first_words+".\n")