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
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	

alt_parshiot = {}
alt_parshiot['Devarim'] = { "nodes": [] }
alt_parshiot['Bamidbar'] = { "nodes": [] }
files = ['Devarim', 'Bamidbar']
heb_files = [u"דברים", u"במדבר"]
alt_perakim = {}
alt_perakim['Devarim'] = { "nodes": [] }
alt_perakim['Bamidbar'] = { "nodes":[] }
prev_perek = ""
def altStructPerek(perakim, para, piska, para_count, prev_ref):
	global prev_perek
	ref = re.compile('[^a-zA-Z]+\(.*?\)')
	spaces = re.compile('[^a-zA-Z]+')
	if ref.match(para):
		ref = ref.match(para).group(0)
		spaces = spaces.match(para).group(0)
		ref = ref.replace(spaces, "")
		ref = ref.replace(")","")
		if len(ref.split(" ")) == 2 and ref.split(" ")[0] == file:
			book, perek = ref.split(" ")
			if perek == "Ibid.":
				perek = prev_perek
			else:
				try:
					perek = int(perek.split(":")[0])
				except:
					pdb.set_trace()
			if not isinstance(perek, int):
				pdb.set_trace()
			ref = "New Sifrei "+file+"."+str(piska)+"."+str(para_count)
			if perek not in perakim:
				if prev_ref != "" and prev_perek in perakim:
					perakim[prev_perek] = (perakim[prev_perek], prev_ref)
				perakim[perek] = ref
			prev_perek = perek

root = JaggedArrayNode()
root.key = 'Sifrei_bamidbar'
root.add_title("New Sifrei Bamidbar", "en", primary=True)
root.add_title(u"ספרי במדבר חדש", "he", primary=True)
root.depth = 2
root.sectionNames = ["Piska", "Paragraph"]
root.addressTypes = ["Integer", "Integer"]
root.validate()
index = {
    "title": "New Sifrei Bamidbar",
    "categories": ["Midrash", "Halachic Midrash"],
    "schema": root.serialize()
}
post_index(index)

root = JaggedArrayNode()
root.key = 'sifrei_devarim'
root.add_title("New Sifrei Devarim", "en", primary=True)
root.add_title(u"ספרי דברים חדש", "he", primary=True)
root.depth = 2
root.sectionNames = ["Piska", "Paragraph"]
root.addressTypes = ["Integer", "Integer"]
root.validate()
index = {
    "title": "New Sifrei Devarim",
    "categories": ["Midrash", "Halachic Midrash"],
    "schema": root.serialize()
}
post_index(index)

print 'indexes'
prev_ref=""
for count, file in enumerate(files):
	prev_perek = 0
	f = open("sifrei_"+file+".txt", 'r')
	is_digit = re.compile('\d+')
	text = {}
	parshiot = [] 
	perakim = {}
	piska = 0
	para_count = 0
	lines = []
	for line in f:
		lines.append(line.replace("\n","").replace("\r",""))
	
	for line_n, line in enumerate(lines):
		if line.find('________________')>=0:
			continue
		if len(line.replace(" ",""))==0:
			continue
		
		if is_digit.match(line):
			piska = int(is_digit.match(line).group(0))
			if not piska in text:
				text[piska] = []
				para_count = 0
			else:
				print 'piska twice'
				pdb.set_trace()
		elif len(line.split(" "))<3: #parsha
			current_parsha = line
			last_one = len(parshiot)
 			if last_one >= 1:
				parshiot[last_one-1] = (parshiot[last_one-1][0], parshiot[last_one-1][1], "New Sifrei "+file+"."+str(piska)+"."+str(para_count))
			if is_digit.match(lines[line_n+1]):
				next_piska = int(is_digit.match(lines[line_n+1]).group(0))
				if next_piska in text:
					print 'next piska found'
					pdb.set_trace()
				
				parshiot.append((current_parsha, "New Sifrei "+file+"."+str(next_piska)+".1"))
			else:
				parshiot.append((current_parsha, "New Sifrei "+file+"."+str(piska)+"."+str(para_count+1)))
		else: #paragraph
			para_count+=1
			altStructPerek(perakim, line, piska, para_count, prev_ref)
			text[piska].append(line)
			prev_ref = "New Sifrei "+file+"."+str(piska)+"."+str(para_count)
			
	last_one = len(parshiot)
	parshiot[last_one-1] = (parshiot[last_one-1][0], parshiot[last_one-1][1], "New Sifrei "+file+"."+str(piska)+"."+str(para_count))
	text_array = convertDictToArray(text)
	send_text = {
			"versionTitle": "New Sifrei "+file,
			"versionSource": "http://www.sefaria.org/",
			"language": "en",
			"text": text_array,
			}
	post_text("New Sifrei "+file, send_text, "on")
	for parsha_tuple in parshiot:
		parsha_name = parsha_tuple[0]
		parsha = ArrayMapNode()
		parsha.add_title(parsha_name, "en", primary=True)
		parsha.add_title(getHebrewParsha(parsha_name), "he", primary=True)
		parsha.key = parsha_name
		parsha.includeSections = True
		parsha.depth = 0
		parsha.addressTypes = []
		parsha.sectionNames = []
		parsha.wholeRef = Ref(parsha_tuple[1]).to(Ref(parsha_tuple[2])).normal()
		parsha.refs = []
		alt_parshiot[file]["nodes"].append(parsha.serialize())

	ref_tuples = convertDictToArray(perakim, empty="")
	first_one = ""
	refs = []
	first_ref = -1
	for count, ref in enumerate(ref_tuples):
		if type(ref) is str:
			refs.append("")
		else:
			start = Ref(ref_tuples[count][0])
			end = Ref(ref_tuples[count][1])
			refs.append(start.to(end).normal())
			if type(first_ref) is int and first_ref == -1:
				first_ref = start
			last_ref = end
	wholeRef = first_ref.to(last_ref).normal()
	for count, ref in enumerate(refs):
		if ref != "":
			chapter_name = "Chapter "+str(count+1)
			chapter = ArrayMapNode()
			chapter.add_title(chapter_name, "en", primary=True)
			chapter.add_title(u"פרק "+numToHeb(count+1), "he", primary=True)
			chapter.key = chapter_name
			chapter.addressTypes = []
			chapter.sectionNames = ["Piska"]
			chapter.includeSections = True
			chapter.refs = []
			chapter.wholeRef = ref
			chapter.depth = 0
			alt_perakim[file]["nodes"].append(chapter.serialize())
	
root = JaggedArrayNode()
root.key = 'Sifrei_bamidbar'
root.add_title("New Sifrei Bamidbar", "en", primary=True)
root.add_title(u"ספרי במדבר חדש", "he", primary=True)
root.depth = 2
root.sectionNames = ["Piska", "Paragraph"]
root.addressTypes = ["Integer", "Integer"]
root.validate()
index = {
    "title": "New Sifrei Bamidbar",
    "categories": ["Midrash", "Halachic Midrash"],
    "alt_structs": {"Parasha": alt_parshiot['Bamidbar'], "Chapters": alt_perakim['Bamidbar']},
    "default_struct": "Chapters",
    "schema": root.serialize()
}
post_index(index)

root = JaggedArrayNode()
root.key = 'sifrei_devarim'
root.add_title("New Sifrei Devarim", "en", primary=True)
root.add_title(u"ספרי דברים חדש", "he", primary=True)
root.depth = 2
root.sectionNames = ["Piska", "Paragraph"]
root.addressTypes = ["Integer", "Integer"]
root.validate()
index = {
    "title": "New Sifrei Devarim",
    "categories": ["Midrash", "Halachic Midrash"],
    "alt_structs": {"Parasha": alt_parshiot['Devarim'], "Chapters": alt_perakim['Devarim']},
    "default_struct": "Chapters",
    "schema": root.serialize()
}
post_index(index)
