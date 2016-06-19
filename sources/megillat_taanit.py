# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys
import codecs
import re
p = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, p)
from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from sefaria.model import *
from sefaria.model.schema import AddressTalmud
from functions import *


text = get_text_plus("Megillat_Taanit/en/Sefaria_Community_Translation")['text']
Megillat_Taanit = open("Megillat_Taanit.txt", 'w')

for ch_count, chapter in enumerate(text):
	Megillat_Taanit.write("Chapter "+str(ch_count+1)+"\n")
	for line_count, line in enumerate(chapter):
		Megillat_Taanit.write("Line "+str(line_count+1)+"\n")
		Megillat_Taanit.write(line.encode('utf-8')+"\n")


Megillat_Taanit.close()