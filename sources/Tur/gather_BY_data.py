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


def goodTag(poss_siman, curr_siman, line, prev_line):
    line = removeAllStrings(line).replace("\r", "").replace("\n", "")
    return abs(poss_siman - curr_siman) <= 10 and len(line) <= 4


if __name__ == "__main__":
    BY_values = {}
    prev_line = ""
    files = ["Even HaEzer/Bi Even HaEzer.txt", "Orach_Chaim/beit yosef orach chaim 1.txt", "Yoreh Deah/beit yosef yoreh deah.txt"]
    for file in files:
        print file
        accum_text = ""
        curr_siman = 0
        for line in open(file):
            line = line.decode('utf-8')
            orig_line = line
            line = line.split(" ")[0]
            if line.find("@22") >= 0 or (line.find("@00") >= 0 and len(line) < 15):
                if line.find("@22") >= 0:
                    poss_siman = re.findall(u"@22[\u05d0-\u05EA]+", line)
                else:
                    poss_siman = re.findall(u"@00[\u05d0-\u05EA]+", line)
                assert len(poss_siman) == 1, "Siman array off {}, {}".format(poss_siman, line.encode('utf-8'), prev_line.encode('utf-8'))

                poss_siman = getGematria(poss_siman[0])
                poss_siman = ChetAndHey(poss_siman, curr_siman)

                if not goodTag(poss_siman, curr_siman, line, prev_line):
                    print line
                    continue

                assert poss_siman > curr_siman, str(poss_siman) + " > " + str(curr_siman)

                if curr_siman > 0:
                    convert = []
                    temp = [each_one for each_one in re.findall(u"\*?\([\u05D0-\u05EA]{1,2}\)", accum_text) if each_one.find(u"שם") == -1]
                    for each_one in temp:
                        convert += [getGematria(each_one)]
                    BY_values[curr_siman] = convert

                curr_siman = poss_siman
                prev_line = orig_line
                accum_text = ""

            accum_text += orig_line + "\n"

        if file.find("Orach") >= 0:
            new_file = codecs.open("orach chaim darchei moshe.txt", 'w', encoding='utf-8')
        elif file.find("Ezer") >= 0:
            new_file = codecs.open("even haezer darchei moshe.txt", 'w', encoding='utf-8')
        elif file.find("Yoreh") >= 0:
            new_file = codecs.open("yoreh deah darchei moshe.txt", 'w', encoding='utf-8')

        new_file.write(json.dumps(BY_values))
        new_file.close()

