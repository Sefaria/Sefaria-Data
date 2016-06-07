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
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud



def create_indexes(sections, eng_helekim, heb_helekim):
  tur = SchemaNode()
  tur.add_title("Tur", 'en', primary=True)
  tur.add_title("Arbah Turim", 'en', primary=False)
  tur.add_title("Arbaah Turim", 'en', primary=False)
  tur.add_title("Arba Turim", 'en', primary=False)
  tur.add_title(u"טור", 'he', primary=True)
  tur.add_title(u"ארבעה טורים", 'he', primary=False)
  tur.key = 'tur'
  for count, helek in enumerate(eng_helekim):
      if helek == "Choshen Mishpat":
          choshen = JaggedArrayNode()
          choshen.add_title("Choshen Mishpat", "en", primary=True)
          choshen.add_title(heb_helekim[count], "he", primary=True)
          choshen.key = helek
          choshen.depth = 2
          choshen.addressTypes = ["Integer", "Integer"]
          choshen.sectionNames = ["Siman", "Seif"]
          tur.append(choshen)
      else:
          helek_node = JaggedArrayNode()
          helek_node.add_title(helek, 'en', primary=True)
          helek_node.add_title(heb_helekim[count], 'he', primary=True)
          helek_node.key = helek
          helek_node.depth = 2
          helek_node.addressTypes = ["Integer", "Integer"]
          helek_node.sectionNames = ["Siman", "Seif"]
          tur.append(helek_node)
  tur.validate()
  index = {
    "title": "Tur",
    "titleVariants": ["Arba Turim", "Arbaah Turim", "Arbah Turim"],
    "categories": ["Halakhah", "Tur and Commentaries"],
    "alt_structs": {"Sections": sections},
    "default_struct": "Siman",
    "schema": tur.serialize()
    }
  post_index(index)


'''
Structure is that for each Helek of Tur, there is a list of nodes named by Hilchot... with a range of
Tur,_(Helek).(Siman_1)-(Siman_2)

'''
sections = {}
sections["nodes"] = []
eng_helekim = ["Orach Chaim", "Yoreh Deah", "Even HaEzer", "Choshen Mishpat"]
heb_helekim = [u"אורח חיים", u"יורה דעה", u"אבן העזר", u"חושן משפט"]

for helek in eng_helekim:
  with open('tur '+helek+'.csv', 'r') as csvfile:
	reader = csv.reader(csvfile)
	for count, row in enumerate(reader):
		if count > 0:
			simanim = row[1]
			first_siman = getGematria(simanim.split("-")[0])
			second_siman = getGematria(simanim.split("-")[1])
			wholeRef = Ref("Tur, "+helek+"."+first_siman+"-"+second_siman)
			node = ArrayMapNode()
			node.add_title(row[0], "he", primary=True)
			node.add_title(row[2], "en", primary=True)
			node.key = row[2]
			node.wholeRef = wholeRef
			node.depth = 0
			node.addressTypes = []
			node.sectionNames = []
			node.refs = []
			sections["nodes"].append(node.serialize())

create_indexes(sections, eng_helekim, heb_helekim)
