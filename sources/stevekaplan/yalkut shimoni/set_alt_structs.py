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

sys.path.insert(0, SEFARIA_PROJECT_PATH)

from sefaria.model import *

def convertIntoRef(line):
	arr = line.split(",")
	parsha = arr[0]
	perek = arr[1]
	remez = arr[2]
	para = arr[3]
	return (perek, Ref("Yalkut Shimoni on Torah, "+parsha+"."+remez+"."+para))

structs = {}
structs = { "nodes" : [] }

f=open("alt_yalkut_genesis.txt", 'r')
line = "nothing"
first_one = ""
last_one = ""
refs = []
while line != '':
	prev_line = line
	line = f.readline()
	start_perek, start_ref = convertIntoRef(line)
	if prev_line == "nothing":
		first_one = (start_perek, start_ref)
	line = f.readline()
	if line != '':
		end_perek, end_ref = convertIntoRef(line)
		last_one = (end_perek, end_ref)
		if start_perek == end_perek:
			try:
				refs.append(start_ref.to(end_ref).normal())
			except:
				pdb.set_trace()
						
whole_ref = first_one[1].to(last_one[1]).normal()
genesis = ArrayMapNode()
genesis.add_title(u"בראשית", "he", primary=True)
genesis.add_title("Bereishit", "en", primary=True)
genesis.key = "bereishit"
genesis.addressTypes = ["Integer"]
genesis.sectionNames = ["Chapter"]
genesis.depth = 1
genesis.wholeRef = whole_ref
genesis.refs = refs
genesis.validate()
structs["nodes"].append(genesis.serialize())
f.close()

f=open("alt_yalkut_exodus.txt", 'r')
line = "nothing"
first_one = ""
last_one = ""
refs = []
while line != '':
	prev_line = line
	line = f.readline()
	start_perek, start_ref = convertIntoRef(line)
	if prev_line == "nothing":
		first_one = (start_perek, start_ref)
	line = f.readline()
	if line != '':
		end_perek, end_ref = convertIntoRef(line)
		last_one = (end_perek, end_ref)
		if start_perek == end_perek:
			refs.append(start_ref.to(end_ref).normal())
		
whole_ref = first_one[1].to(last_one[1]).normal()
exodus = ArrayMapNode()
exodus.add_title(u"שמות", "he", primary=True)
exodus.add_title("Shemot", "en", primary=True)
exodus.key = "shemot"
exodus.addressTypes = ["Integer"]
exodus.sectionNames = ["Chapter"]
exodus.depth = 1
exodus.wholeRef = whole_ref
exodus.refs = refs
exodus.validate()
structs["nodes"].append(genesis.serialize())
f.close()


f=open("alt_yalkut_numbers.txt", 'r')
line = "nothing"
first_one = ""
last_one = ""
refs = []
while line != '':
	prev_line = line
	line = f.readline()
	start_perek, start_ref = convertIntoRef(line)
	if prev_line == "nothing":
		first_one = (start_perek, start_ref)
	line = f.readline()
	if line != '':
		end_perek, end_ref = convertIntoRef(line)
		last_one = (end_perek, end_ref)
		if start_perek == end_perek:
			refs.append(start_ref.to(end_ref).normal())
		
whole_ref = first_one[1].to(last_one[1]).normal()
numbers = ArrayMapNode()
numbers.add_title(u"במדבר", "he", primary=True)
numbers.add_title("Bamidbar", "en", primary=True)
numbers.key = "bamibdar"
numbers.addressTypes = ["Integer"]
numbers.sectionNames = ["Chapter"]
numbers.depth = 1
numbers.wholeRef = whole_ref
numbers.refs = refs
numbers.validate()
structs["nodes"].append(genesis.serialize())
f.close()


f=open("alt_yalkut_deut.txt", 'r')
line = "nothing"
first_one = ""
last_one = ""
refs = []
while line != '':
	prev_line = line
	line = f.readline()
	start_perek, start_ref = convertIntoRef(line)
	if prev_line == "nothing":
		first_one = (start_perek, start_ref)
	line = f.readline()
	if line != '':
		end_perek, end_ref = convertIntoRef(line)
		last_one = (end_perek, end_ref)
		if start_perek == end_perek:
			refs.append(start_ref.to(end_ref).normal())
		
whole_ref = first_one[1].to(last_one[1]).normal()
deut = ArrayMapNode()
deut.add_title(u"דברים", "he", primary=True)
deut.add_title("Devarim", "en", primary=True)
deut.key = "deut"
deut.addressTypes = ["Integer"]
deut.sectionNames = ["Chapter"]
deut.depth = 1
deut.wholeRef = whole_ref
deut.refs = refs
deut.validate()
structs["nodes"].append(genesis.serialize())
f.close()


root = SchemaNode()
root.add_title("Yalkut Shimoni on Torah", "en", primary=True)
root.add_title(u"ילקוט שמעוני על התורה", "he", primary=True)
root.key = "yalkut"

root.validate()

index = {
	"title": "Yalkut Shimoni on Torah",
	"categories": ["Midrash"],
	"alt_structs": {"Chapters": structs},
	"default_struct": "Parasha",
	"schema": root.serialize()
}


post_index(index)
