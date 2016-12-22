# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
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
sys.path.insert(0,p+"/sources")
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
sys.path.append(p+"/data_utilities")
from data_utilities.dibur_hamatchil_matcher import *
from functions import *


sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud


def getKeys(fname):
    reg = re.compile(ur"\[[\u05d0-\u05ea]{1,3}\].*?")
    text = {}
    prev_key = 0
    f = open(fname)
    for line in f:
        print fname
        print line
        line = line.decode('utf-8')
        line = line.replace("\n","")
        match = reg.search(line)
        if len(line) > 0 and match:
            actual_match = match.group(0)
            key = getGematria(actual_match)
            assert key not in text, key
            assert abs(key-prev_key) < 15, "{} {}".format(key, prev_key)
            text[key] = line.replace(actual_match+" ", "")
            prev_key = key
    return text

def post_links(positive, negative):
    pos_links = []
    neg_links = []
    for index, line in enumerate(positive):
        pos_links.append({
                "refs": [
                             "Sefer Mitzvot Gadol, Volume Two.{}".format(index+1),
                            "Sefer Mitzvot Gadol, Volume Two, Remazim.{}".format(index+1)
                        ],
                "type": "commentary",
                "auto": True,
                "generated_by": "smag"})

    for index, line in enumerate(negative):
        neg_links.append({
                "refs": [
                             "Sefer Mitzvot Gadol, Volume One.{}".format(index+1),
                            "Sefer Mitzvot Gadol, Volume One, Remazim.{}".format(index+1)
                        ],
                "type": "commentary",
                "auto": True,
                "generated_by": "smag"})
    print len(pos_links)
    print len(neg_links)
    post_link(pos_links+neg_links)


if __name__ == "__main__":
    positive = convertDictToArray(getKeys("Remazim Positive.txt"), empty="")
    negative = convertDictToArray(getKeys("Remazim Negative.txt"), empty="")
    send_text = {
        "language": "he",
        "text": positive,
        "versionTitle": "Munkatch, 1901",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637"
    }
    post_text("SeMaG, Volume Two, Remazim", send_text)
    send_text = {
        "language": "he",
        "text": negative,
        "versionTitle": "Munkatch, 1901",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637"
    }
    post_text("SeMaG, Volume One, Remazim", send_text)

    post_links(positive, negative)






