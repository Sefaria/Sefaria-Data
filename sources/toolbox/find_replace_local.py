# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import sys
import re

import csv
import argparse
import pdb

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-f", "--file", help="File that has text that needs to be replaced.", default="")
	parser.add_argument("-o", "--old_text", help="Old text.", default="")
	parser.add_argument("-n", "--new_text", help="New text.", default="")
	args = parser.parse_args()
	
	f = open(args.file, 'r')
	old_text = args.old_text
	new_text = args.new_text
	contents = ""
	for line in f:
		if line.find(old_text)>=0:
			line = line.replace(old_text, new_text)
			print "Replaced "+old_text+" with "+new_text
		contents += line
	
	f.close()
	f = open(args.file, 'w')
	f.write(contents)	
	
	
	#python find_replace_local.py -f "Tur/OrachChaim/bach orach chaim helek a.txt" -o "@77@22תרמ @33ולענין " -n "@77@22תרט @33ולענין "