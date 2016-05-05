# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys
import re
import csv
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *
from sefaria.sheets import save_sheet


sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud

all_books = library.all_index_records()
'''
for each commentary, grab LinkSet
'''

books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
commentaries = ["Abarbanel",
                "Abravanel",
                "Baal HaTurim",
                "Chizkuni",
                "Daat Zkenim",
                "Haamek Davar",
                "Ibn Ezra",
                "Ikar Siftei Hachamim",
                "Kitzur Baal Haturim",
                "Kli Yakar",
                "Malbim",
                "Malbim Beur Hamilot",
                "Metzudat David",
                "Metzudat Zion",
                "Or HaChaim",
                "Penei Dovid",
                "Rabbeinu Bachya",
                "Rabbeinu Chananel",
                "Radak",
                "Ralbag",
                "Ramban",
                "Rashbam",
                "Rashi",
                "Saadia Gaon",
                "Sepher Torat Elohim",
                "Sforno",
                "Shadal",
                "Torah Temimah",
                "Tiferet Yisrael",
                "Toldot Aharon",
                "Akeidat Yitzchak",
                "Meshech Hochma",
                "Shney Luchot HaBrit"
                ]
dict_refs = {}
probs = open('probs.txt','w')
max = 0
top_refs = []
csvf = open('d3_data.csv', 'w')
csvwriter = csv.writer(csvf, delimiter=';')
csvwriter.writerow(["Ref", "Number"])
for book in books:
    book = library.get_index(book)
    refs = book.all_segment_refs()
    for ref in refs:
        count_arr = []
        for link in LinkSet(ref).array():
            if link.contents()['type'] == 'commentary': #if there is time make sure three parshanut ones are included as they
                                                        #dont have commentary type
                which_one = link.contents()['refs']
                if which_one[0].find(' on ')>=0:
                    this_commentary = which_one[0].split(" on ")[0]
                elif which_one[1].find(' on ')>=0:
                    this_commentary = which_one[1].split(" on ")[0]
                else:
                    continue

                if this_commentary in commentaries:
                    if this_commentary not in count_arr:
                        count_arr.append(this_commentary)
                else:
                    probs.write(str(link.contents()['refs'])+'\n\n')
        sum = len(count_arr)
        if sum > max:
            max = sum
        if sum >= 13:
            top_refs.append(ref)
        dict_refs[ref] = sum
        csvwriter.writerow([str(ref).replace(' ','_'), str(dict_refs[ref])])
csvf.close()
print max
sheet = {
		"title": "Chumash Passages Most Commented On",
		"sources": [{"ref": ref.normal()} for ref in top_refs],
		"options": {"numbered": 1, "divineNames": "noSub"}
	}
save_sheet(sheet, 1)
