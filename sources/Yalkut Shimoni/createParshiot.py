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
b_parshiot = ["breshit", "noach", "lechlecha", "vayira", "chaisara", "toldot", "vayetse", "vayishlach", 
"vayeshev", "mekatz", "vayegash", "vayechi"]
e_parshiot = ["shemot", "vaera", "bo", "beshalach", "yitro", "mishpatim", "terumah",
"titsaveh", "kitisa", "vayakhel", "pikudei"]
v_parshiot = ["vayikra", "tsav", "shemini", "tazrea", "metzora", "acharei", "kedoshim", "emor", "behar", "behukotai"]
n_parshiot = ["bamidbar", "naso", "behalotcha", "shelach", "korach", "hukat", "balak", "pinchas", "matot", "masai"]
d_parshiot = ["devarim", "vaetchanan", "ekev", "raeh", "shoftim", "kitetsa", "kitavo", "nitzavim", "vayelech",
"hazinu", "bracha"]
parshiot = b_parshiot+e_parshiot+v_parshiot+n_parshiot+d_parshiot

actual_spellings = ["Bereishit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach",
"Vayeshev", "Miketz", "Vayigash", "Vayechi", "Shemot", "Vaera", "Bo", "Beshalach", "Yitro",
"Mishpatim", "Terumah", "Tetzaveh", "Ki Tisa", "Vayakhel", "Pekudei", "Vayikra", "Tzav", "Shmini",
"Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar", "Bechukotai", "Bamidbar", "Nasso",
"Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei",
"Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo", "Nitzavim", "Vayeilech", "Ha'Azinu",
"V'Zot HaBerachah"]


for parsha_count, parsha in enumerate(parshiot):
	html = urllib.urlopen("http://www.tsel.org/torah/yalkutsh/"+parsha+".html")
	html_text = str(BeautifulSoup((html.read())))
	text_arr = html_text.split("""<h1 id="A""")
	actual_text = ""
	len_arr = len(text_arr)-1
	for count, the_text in enumerate(text_arr):
		if count > 0:
			if count == len_arr:
				actual_text += """<h1 id="A""" + the_text.split("</b></font>")[0]
			else:
				actual_text += """<h1 id="A"""+ the_text
	
	if os.path.exists(actual_spellings[parsha_count]+".txt") == True:
		os.remove(actual_spellings[parsha_count]+".txt")	
	f = open(actual_spellings[parsha_count]+".txt", "w")
	actual_text = actual_text.replace("</p>", "")
	actual_text = actual_text.replace("<p>", "\n")
	f.write(actual_text)
	f.close()