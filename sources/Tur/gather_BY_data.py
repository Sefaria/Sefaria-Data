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
            if line.find("@22") >= 0 or (line.find("@00") >= 0 and len(line) < 15):
                if line.find("@22") >= 0:
                    poss_siman = re.findall(u"@22[\u05d0-\u05EA]+", line)
                else:
                    poss_siman = re.findall(u"@00[\u05d0-\u05EA]+", line)
                assert len(poss_siman) == 1, "Siman array off {}".format(poss_siman)
                poss_siman = getGematria(poss_siman[0])


                #two cases to switch: daled and then chet becomes hey, curr_siman - 4 == poss_siman - 8, poss_siman = poss_siman - 8 + 5
                ##  or hey after zion becomes chet, if curr_siman - 7 == poss_siman - 5, poss_siman = poss_siman - 5 + 8
                if curr_siman - 4 == poss_siman - 8:
                    poss_siman = poss_siman - 3
                if curr_siman - 7 == poss_siman - 5:
                    poss_siman = poss_siman + 3

                assert poss_siman > curr_siman, str(poss_siman) + " > " + str(curr_siman)
                if curr_siman > 0:
                    convert = []
                    temp = [each_one for each_one in re.findall(u"\([\u05D0-\u05EA]{1,2}\)", accum_text) if each_one.find(u"שם") == -1]
                    for each_one in temp:
                        convert += [getGematria(each_one)]
                    BY_values[curr_siman] = convert

                curr_siman = poss_siman
                accum_text = ""

            accum_text += line + "\n"

        if file.find("Orach") >= 0:
            new_file = codecs.open("orach chaim darchei moshe.txt", 'w', encoding='utf-8')
        elif file.find("Ezer") >= 0:
            new_file = codecs.open("even haezer darchei moshe.txt", 'w', encoding='utf-8')
        elif file.find("Yoreh") >= 0:
            new_file = codecs.open("yoreh deah darchei moshe.txt", 'w', encoding='utf-8')

        new_file.write(json.dumps(BY_values))
        new_file.close()

