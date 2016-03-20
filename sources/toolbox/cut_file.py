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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Title of input file to be divided in half.")
    parser.add_argument("--first_half", help="Title of file to put the first half of the original file.")
    parser.add_argument("--second_half", help="Title of file to put the second half of the original file.")
    parser.add_argument("--where", help="String that identifies where the original file should be split.")
    args = parser.parse_args()
    where = args.where
    if where:
    	file = open(args.file, 'r')
    	where_pos = -1
    	for count, line in enumerate(file):
    		if line.find(where)>=0:
    			where_pos = count
    			break
    	print where_pos
    	first_half = open(args.first_half, 'w')
    	second_half = open(args.second_half, 'w')
    	file.close()
    	file = open(args.file, 'r')
    	for count, line in enumerate(file):
    		if count < where_pos:
    			first_half.write(line)
    		else:
    			second_half.write(line)
    	first_half.close()
    	second_half.close()
    	file.close()