# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
from urllib.error import URLError, HTTPError
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
	parser.add_argument("-f1", "--file_1", help="File that will be pasted into the end file first.", default="")
	parser.add_argument("-f2", "--file_2", help="File that will be pasted into the end file second.", default="")
	parser.add_argument("-e", "--end_file", help="New file that will contain both files 1 and 2.", default="")

	args = parser.parse_args()
	
	f1 = open(args.file_1, 'r')
	f2 = open(args.file_2, 'r')
	contents_f1 = ""
	contents_f2 = ""
	for line in f1:
		contents_f1 += line
	for line in f2:
		contents_f2 += line
	
	f1.close()
	f2.close()
	end_file = open(args.end_file, 'w')

	
	end_file.write(contents_f1)
	end_file.write(contents_f2)