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

root = SchemaNode()
root.add_title("Brit Moshe", "en", primary=True)
root.add_title(u"ברית משה", "he", primary=True)
root.key = "britmoshe"


vol1 = JaggedArrayNode()
vol1.key = 'vol1'
vol1.add_title("Volume One", "en", primary=True)
vol1.add_title(u"חלק "+numToHeb(1), "he", primary=True)
vol1.depth = 3
vol1.sectionNames = ["Mitzvah", "Comment", "Paragraph"]
vol1.addressTypes = ["Integer", "Integer", "Integer"]




vol2 = JaggedArrayNode()
vol2.key = 'vol2'
vol2.add_title("Volume Two", "en", primary=True)
vol2.add_title(u"חלק "+numToHeb(2), "he", primary=True)
vol2.depth = 3
vol2.sectionNames = ["Mitzvah", "Comment", "Paragraph"]
vol2.addressTypes = ["Integer", "Integer", "Integer"]



root.append(vol1)
root.append(vol2)
root.validate()
index = {
    "title": "Brit Moshe",
    "categories": ["comment_indexary2", "Halakhah", "Sefer Mitzvot Gadol"],
    "schema": root.serialize()
    }
#post_index(index)
for count, fname in enumerate(["Brit Moshe vol 1.txt", "Brit Moshe vol 2.txt"]):
    if count == 0:
        continue
    f = open(fname, 'r')
    volume = "Volume Two" if count == 1 else "Volume One"
    print volume
    print fname
    current_mitzvah = 1
    text = {}
    text[current_mitzvah] = []
    comment_index = -1
    prev_line = ""
    for line in f:
        actual_line = line
        line=line.replace("\n","")
        line = line.decode('utf-8')
        if line.find("@22")>=0:
            line = line.replace(")","").replace(" ","")
            new_comment_index = getGematria(line)
            assert len(text[current_mitzvah]) == comment_index + 1, "{} {}".format(len(text[current_mitzvah]), comment_index)
            for i in range(new_comment_index-len(text[current_mitzvah])):
                text[current_mitzvah].append([])
                comment_index = len(text[current_mitzvah])-1
                text[current_mitzvah][comment_index] = []
        elif line.find(u"@88מצוה לא תעשה ")>=0 or line.find(u"@02מצות עשה ")>=0:
            print line
            line = line.replace(u" לא", u"")
            if line[0] == ' ':
                line = line[1:]
            if line[len(line)-1] == ' ':
                line = line[0:len(line)-1]
            words = line.split(" ")[2:]
            print words
            if len(words) == 1:
                current_mitzvah = getGematria(words[0])
                assert type(current_mitzvah) is int, current_mitzvah
                text[current_mitzvah] = []
                comment_index = -1
            elif words[1].find(u"עד")>=0:
                beg, end = words[0], words[2]
                beg = getGematria(beg)
                end = getGematria(end)
                assert type(beg) is int, beg
                assert type(end) is int, end
                assert beg < end, "beg {} end {}".format(beg, end)
                all = ""
                for i in range(end-beg):
                    text[i+beg] = []
                    text[i+beg].append([])
                    text[i+beg][0].append(u"ראו מצוה "+str(end))
                    if i==end-beg-1:
                        all += str(i+beg)
                    else:
                        all += str(i+beg)+", "
                text[end] = []
                text[end].append([])
                text[end][0].append(u"מצוות "+all)
                current_mitzvah = end
                comment_index = 0
            elif len(words) > 1:
                mitzvah_one = getGematria(words[0])
                mitzvah_two = getGematria(words[1])
                assert type(mitzvah_one) is int, mitzvah_one
                assert type(mitzvah_two) is int, mitzvah_two
                text[mitzvah_one] = []
                text[mitzvah_two] = []
                text[mitzvah_one].append([])
                text[mitzvah_two].append([])
                text[mitzvah_one][0].append(u"ראו מצוה "+str(mitzvah_two))
                text[mitzvah_two][0].append(u"מצוות "+str(mitzvah_one)+u" ו"+str(mitzvah_two))
                current_mitzvah = mitzvah_two
                comment_index = 0
        else:
            if line.find("@33")>=0 and line.find("@11")>=0:
                line = line.replace("@11", "<b>")
                line = line.replace("@33", "</b>")
            line = line.replace("@00","").replace("@99","")
            line = line.replace("@66", "").replace("@55","").replace("@44","")
            text[current_mitzvah][comment_index].append(line)
        prev_line = actual_line


    text_array = convertDictToArray(text)
    send_text = {
            "versionTitle":  "Munkatch, 1901",
            "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637",
            "tdraext": text_array,
            "language": "he"
            }

    post_text("Brit Moshe, {}".format(volume), send_text)
    links = []
    for mitzvah in text:
        mitzvah_text = text[mitzvah]
        for count, each_comment_index in enumerate(mitzvah_text):
            for line_count, each_line in enumerate(each_comment_index):
                links.append({
                    "refs": [
                             "Brit Moshe, {}.{}.{}.{}".format(volume, mitzvah, count+1, line_count+1),
                            "Sefer Mitzvot Gadol, {}.{}".format(volume, mitzvah)
                        ],
                    "type": "comment_indexary",
                    "auto": True,
                    "generated_by": "Brit Moshe to SEMAG linker"
                 })
    #post_link(links)
