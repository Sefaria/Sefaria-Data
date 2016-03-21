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


files = ["sanhedrin", "ketubot"]
marker = '@11דף'
for file in files:
	f = open(file+'.txt', 'r')
	new_file = open(file+'2.txt','w')
	for line in f:
		if line.find(marker)>=0:
			if line.find(marker) != line.rfind(marker):
				lines = []
				while line.find(marker) != line.rfind(marker):
					pos = line.rfind(marker)
					lines.append(line[pos:])
					line = line[0:pos]
				len_lines = len(lines)
				new_file.write(line)
				new_file.write('\n')
				for i in range(len_lines):
					new_file.write(lines[len_lines-i-1])
					new_file.write('\n')
			else:
				new_file.write(line)
				print "line"
		else:
			new_file.write(line)
			print "line"
	new_file.close()


files = ["bava batra", "bava metzia", "beitzah", "gittin", "shabbat", "ketubot", "sanhedrin", "bava kamma", "zevachim", "chullin"]
new_files = []
p = re.compile('@\d\dע"\ב')
for file in files:
	new_file = open(file+"2.txt", 'w')
	f = open(file+".txt", 'r')
	for line in f:
		no_match = True
		words = line.split(" ")
		for word in words:
			if p.match(word):
				no_match = False
				match = p.match(word).group(0)
				paras = line.split(match)
				if len(paras) == 3 and len(paras[0])==0:
					para_0 = paras[1]
					para_1 = paras[2]
				elif len(paras) == 2:
					para_1 = paras[1]
					para_0 = paras[0]
					
				if len(paras)==1:
					new_file.write(para_0)
				elif len(paras)==2:
					new_file.write(para_0)
					new_file.write("\n")
					if para_1.find("@55")==0:
						print "yes"
						para_1 = para_1[3:]
					para_1 = "@11"+para_1
					#second and third word may have tags
					words_para = para_1.split(" ")
					para_1 = ""
					count = 0
					for count, word in enumerate(words_para):
						if count == 1 or count == 2:
							para_1 += word.replace("@55","").replace("@44","").replace("@77","") + " "
						else:
							para_1 += word + " "	
					new_file.write(para_1)
				elif len(paras)>2 and len(paras[0])>0:
					pdb.set_trace()
				break
		if no_match:
			new_file.write(line)
	new_file.close()
