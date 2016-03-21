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



if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("title", help="Name of input file.")
	parser.add_argument("-s", "--separator", help="The separator of the regular expressions. Default is a semi-colon.", default=";")
	parser.add_argument("--reg_exps", help="Regular expressions that every line of text must conform to.  They are inputted via a string whereby each reg exp"+
		" is separated by a semi-colon.  If there is a semi-colon in one of the reg exps, specify a different separator by '--separator [new_separator]'")
	parser.add_argument("-f", "--output_file", help="Name of output file.")
	args = parser.parse_args()
	output_file = open(args.output_file, 'w')
	if args.reg_exps:
		string_list = args.reg_exps.split(args.separator)
		reg_exps_list = []
		for reg_exp in string_list:
			reg_exps_list.append(re.compile(reg_exp))
		for line in open(args.title):
			for count, reg_exp in enumerate(reg_exps_list):
				this_one = False
				if reg_exp.match(line):
					this_one = True
				if this_one == False:
					output_file.write(line+"\n")
