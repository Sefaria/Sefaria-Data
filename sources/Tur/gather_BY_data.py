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
from sefaria.model import *
from sefaria.model.schema import AddressTalmud

if __name__ == "__main__":
    BY_values = {}
    files = ["Even HaEzer/Bi Even HaEzer.txt", "Orach_Chaim/beit yosef orach chaim.txt", "Yoreh Deah/beit yosef yoreh deah.txt"]
    for file in files:
        print file
        accum_text = ""
        curr_siman = 0
        for line in open(file):
            line = line.decode('utf-8')
            if line.find("@22") >= 0:
                poss_siman = re.findall(u"@22[\u05d0-\u05EA]+", line)
                assert len(poss_siman) == 1, "Siman array off " + str(poss_siman)
                poss_siman = getGematria(poss_siman[0])
                print line
                print file

                #two cases to switch: daled and then chet becomes hey, curr_siman - 4 == poss_siman - 8, poss_siman = poss_siman - 8 + 5
                ##  or hey after zion becomes chet, if curr_siman - 7 == poss_siman - 5, poss_siman = poss_siman - 5 + 8
                if curr_siman - 4 == poss_siman - 8:
                    poss_siman = poss_siman - 3
                if curr_siman - 7 == poss_siman - 5:
                    poss_siman = poss_siman + 3

                assert poss_siman > curr_siman, str(poss_siman) + " > " + str(curr_siman)
                if curr_siman > 0:
                    BY_values[curr_siman] = re.findall(u"\([\u05D0-\u05EA]{1,4}\)", accum_text)
                curr_siman = poss_siman
                accum_text = ""

            accum_text += line + "\n"

        new_file = codecs.open(file.replace(".txt", "_data.txt"), 'w', encoding='utf-8')
        new_file.write(json.dumps(BY_values))
        new_file.close()

