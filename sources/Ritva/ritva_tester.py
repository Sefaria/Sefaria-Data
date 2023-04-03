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
from parsing_utilities import util, sanity_checks
from parsing_utilities.sanity_checks import TagTester
from functions import *
from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *


def perek_checker(prev_val, curr_val):
	return (curr_val > prev_val)

def checkPerakim(files):
	for file in files:
		if file == "Berakhot":
			continue
		print file
		reg = u'(?:@00\u05e4\u05e8\u05e7 |@00\u05e4")([\u05d0-\u05ea]+)'
		open_file = open(file+".txt")
		tt = TagTester("@00", open_file, reg=reg)
		result = tt.in_order_one_section(1, perek_checker)
		print result


def check_all_11s(files):
	problem_file = open("11_33_exceptions.txt", 'w')
	for file in files:
		for line in open(file+".txt"):
			if line.find("@11") == 0 and line.find("@33") == -1:
				problem_file.write(line+"\n")


def check_all_exceptions(files):
	problem_file = open("all_tag_exceptions.txt", 'w')
	for file in files:
		for line in open(file+".txt"):
			if line.find("@22") == -1 and line.find("@11") == -1 and line.find("@00") == -1:
				problem_file.write(line+"\n")


def check_all_00s(files):
	problem_file = open("00_exceptions.txt", 'w')
	for file in files:
		for line in open(file+".txt"):
			if line.find("@00") >= 0 and line.find("פרק") == -1:
				problem_file.write(line+"\n")


def check_all_22s(files):
	problem_file = open("22_exceptions.txt", 'w')
	for file in files:
		for line in open(file+".txt"):
			if line.find("@22") >= 0:
				definitely_daf = line.find("דף") >= 0 or line.find('ע"ב') >= 0 or line.find('ע"א') >= 0
				if not definitely_daf:
					len_line = len(line.replace("@22", "").replace(" ","").replace('"','').replace('\n',''))
					if len_line == 0 or len_line > 4:
						problem_file.write(line+"\n")



def checkDappim(files):
	errors = open('daf_issues.txt', 'w')
	for file in files:
		print file
		flagged = []
		errors.write("\n"+file+"\n")
		reg = u'@22\[?[\u05d0-\u05ea\s"]+\]?'
		open_file = open(file+".txt")
		tt = TagTester("@22", open_file, reg=reg)
		num_array, string_array = tt.daf_processor()
		prev_value = 2
		for count, this_value in enumerate(num_array):
			if this_value - prev_value <= 0:
				flagged.append(string_array[count])
			prev_value = this_value
		errors.write("Flagged mistakes: "+"\n")
		flagged_str = ""
		for each_one in flagged:
			flagged_str += each_one.replace("\n","").replace("@22", "")+",  "
		errors.write(flagged_str.encode('utf-8')+"\n")
		errors.write("All Dappim in this Masechet: "+"\n")
		dappim_str = ""
		for each_one in string_array:
			dappim_str += each_one.replace("\n", "").replace("@22", "")+",   "
		errors.write(dappim_str.encode('utf-8')+"\n")
	errors.close()
	#check that we go in order, redo above test
	#check that nothing is missing, redo above test except that we dont want it to fail 
	#separate function print the dappim headers into a file




if __name__ == "__main__":
	
	files = ["Sukkah", "Berakhot", "Megillah", "Moed Katan", "Yoma", "Rosh Hashanah", "Taanit", "Niddah"]
	checkPerakim(files)
	checkDappim(files)
	check_all_22s(files)
	check_all_00s(files)
	check_all_exceptions(files)
	check_all_11s(files)