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
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)

os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)


if __name__ == "__main__":
  files = []
  if sys.argv[1] == 'Drisha':
    files_helekim = ["Orach_Chaim/drisha orach chaim helek a.txt", "yoreh deah/drisha yoreh deah.txt",
   "Even HaEzer/drisha even haezer.txt"]
  elif sys.argv[1] == 'Prisha':
    files_helekim = ["Orach_Chaim/prisha orach chaim.txt", "yoreh deah/prisha yoreh deah.txt",
   "Even HaEzer/prisha even haezer.txt"]
  elif sys.argv[1].find("DarcheiMoshe")>=0:
    files_helekim = ["Orach_Chaim/darchei moshe orach chaim.txt", "yoreh deah/darchei moshe yoreh deah.txt",
    "Even HaEzer/darchei moshe even haezer.txt"]

  for file in files_helekim:
        open_file = open(file)
        text = {}
        siman = 0
        prev_line_siman = ""
        for line in open_file:
            print file
            print line
            orig_line = line
            line = line.decode('utf-8')
            line = line.replace("\n", "").replace("\r","")

            has_brackets = line.find("[") >= 0 and line.find("]") >= 0
            has_parenthesis = line.find("(") >= 0 and line.find(")") >= 0
            if line.find(" ") == 0:
                line = line[1:]
            if has_brackets or has_parenthesis:
                assert siman > 0
                text[siman] += 1
            if line.find("@22") in [0, 1] and len(line) > 3:
                line = line.replace(u"@22סי' ", "").replace(u"@22ס' ","").replace(u"@22סי ","").replace("@22", "")
                poss_siman = getGematria(line.split(" ")[0])
                if abs(poss_siman - siman) > 60 or poss_siman <= siman or len(line.split(" ")[0]) > 4:
                    continue
                siman = poss_siman
                text[siman] = 0
                prev_line_siman = orig_line


        if file.find("yoreh") >= 0:
            helek = "_YorehDeah"
        elif file.find("Even") >= 0:
            helek = "_EvenHaEzer"
        else:
            helek = "_OrachChaim"
        dump_file = open(sys.argv[1]+helek+"_length_siman.txt", 'w')
        dump_file.write(json.dumps(text))
        dump_file.close()











