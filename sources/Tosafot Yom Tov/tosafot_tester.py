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
from data_utilities.sanity_checks import TagTester
from functions import *
from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *



def checkPerakim():
	for file in glob.glob(u"*.txt"):
		if file.find("intro") == -1:
			print file
			reg = u'(?:@00\u05e4\u05e8\u05e7 |@00\u05e4")([\u05d0-\u05ea]+)'
			open_file = open(file)
			tt = TagTester("@00", open_file, reg=reg)
			result = tt.in_order_one_section(1)
			if result[0] != "SUCCESS":
				pdb.set_trace()

def checkMishnayot():
	for file in glob.glob(u"*.txt"):
		if file.find("intro") == -1:
			print file
			reg = u'@22.*?[\u05d0-\u05ea]+.*?'
			open_file = open(file)
			tt = TagTester("@22", open_file, reg=reg)
			result = tt.in_order_many_sections(end_tag="@00")
			if result[0] != "SUCCESS":
				pdb.set_trace()


def get_mishnah_perek_lengths():
	mishnah_lengths = {}
	mishnah_list = library.get_indexes_in_category("Mishnah")
	for mishnah in mishnah_list:
		text = get_text_plus(mishnah+"/he/Vilna_Mishna", 'draft')
		length_draft = text['lengths'][0]
		mishnah_lengths[mishnah] = length_draft
	return mishnah_lengths


def get_TYT_perek_lengths():
	TYT_lengths = {}
	for file in glob.glob(u"*.txt"):
		if file.find("intro") == -1:
			reg = u'(?:@00\u05e4\u05e8\u05e7 |@00\u05e4")([\u05d0-\u05ea]+)'
			open_file = open(file)
			tt = TagTester("@00", open_file, reg=reg)
			TYT_perakim = tt.in_order_one_section(1)
			if TYT_perakim[0] == "SUCCESS":
				len_TYT_perakim = len(TYT_perakim[1])
			if file.find("avot") >= 0:
				mishnah_name = "Pirkei Avot"
			else:
	 			mishnah_name = "Mishnah "+file.replace(".txt", "").title()
	 		mishnah_name = mishnah_name.replace("_", " ")
			TYT_lengths[mishnah_name] = len_TYT_perakim
	return TYT_lengths


def check_lengths(TYT_lengths, mishnah_lengths):
	others = ["Pirkei Avot", "Mishnah Bikkurim"]
	for mishnah in TYT_lengths:
		if TYT_lengths[mishnah] != mishnah_lengths[mishnah]:
			print mishnah
		

def get_num_mishnayot_per_perek():
	num_mishnayot = {}
	mishnah_list = library.get_indexes_in_category("Mishnah")
	for masechet in mishnah_list:
		mishnah_text = get_text_plus(masechet+"/he/Vilna_Mishna", 'draft')['he']
		num_mishnayot[masechet] = []
		for perek in mishnah_text:
			num_mishnayot[masechet].append(len(perek))
	return num_mishnayot

def get_num_TYTs_per_perek():
	num_TYTs = {}
	actual_TYTs = {}
	for file in glob.glob(u"*.txt"):
		if file.find("intro") == -1:
			reg = u'@22.*?[\u05d0-\u05ea]+.*?'
			open_file = open(file)
			tt = TagTester("@22", open_file, reg=reg)
			headers = tt.in_order_many_sections(end_tag="@00")
			if headers[0] == "SUCCESS":
				headers = headers[1]
			else:
				pdb.set_trace()
			if file.find("avot") >= 0:
				masechet = "Pirkei Avot"
			else:
	 			masechet = "Mishnah "+file.replace(".txt", "").replace("_"," ").title()
	 		num_TYTs[masechet] = []
	 		actual_TYTs[masechet] = headers
	 		for perek in headers:
	 			num_TYTs[masechet].append(len(perek))
	return num_TYTs, actual_TYTs

alreadyFound = {}


def check_TYT_and_mishnayot():
	how_many = 0
	issues = open("issues", 'w')
	num_TYTs, actual_TYTs = get_num_TYTs_per_perek()
	num_mishnayot = get_num_mishnayot_per_perek()
	for masechet in sorted(num_TYTs.keys()):
		print masechet
		for perek in range(len(num_TYTs[masechet])):
			if (masechet + str(perek)) in alreadyFound:
				continue
			mishnah = num_mishnayot[masechet][perek]
			TYT = num_TYTs[masechet][perek]
			try:
				if TYT != mishnah:
					how_many += 1
					alreadyFound[masechet + str(perek)] = True
					issues.write(masechet+", perek "+str(perek+1)+", mishnah_count "+str(mishnah)+", TYT count "+str(TYT)+"\n")
					issues.write("The Tosafot Yom Tov tags are the following: \n")
					for each_one in actual_TYTs[masechet][perek]:
						issues.write(each_one.encode('utf-8')+", ")
					issues.write("\n\n\n\n")
			except:
				pdb.set_trace()
	print how_many
	issues.close()
'''
For each perek in TYT_lengths, create dictionary like TYT_mishnayot[masechet][perek] = num_mishnayot

'''


def perek_checker(curr_val, prev_val):
	return (curr_val >= prev_val)

if __name__ == "__main__":
	checkPerakim()
	checkMishnayot()
	check_TYT_and_mishnayot()

	
	
		





