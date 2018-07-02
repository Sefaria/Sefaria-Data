# -*- coding: utf-8 -*-
__author__ = 'eliav'
import re
import json
import urllib2
import sys
from fuzzywuzzy import fuzz
sys.path.insert(1,'../genuzot')
import helperFunctions as Helper
import hebrew

def book_record():
      return {
    "title" : "Rif on Taanit",
    "categories" : [
        "Other",
        "Rif"
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Rif on Taanit",
                "primary" : True
            },
            {
                "lang" : "he",
                "text" : 'הריף על תענית',
                "primary" : True
            }
        ],
        "nodeType" : "JaggedArrayNode",
        "depth" : 2,
        "sectionNames" : [
            "Daf",
            "Peirush"
        ],
        "addressTypes" : [
           "Integer",
            "Integer"
        ],
        "key" : "Rif on Taanit"
    }
	}


def open_file():
    with open("source/rif_taanit.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        return ucd_text


def list_tags(text):
    data = re.findall(r'@[0-9][0-9]', text)
    tags_list = dict((x, data.count(x)) for x in data)
    return tags_list


def parse(text):
    rif = []
    sugiyot = re.split(ur'@44([^@]*)',text)
    for sug, text in zip(sugiyot[1::2], sugiyot[2::2]):
        cut = re.split(":", text)
        page = []
        sug = re.sub(u"[\u00B0\*]", "", sug)
        page.append(sug)
        for part in cut:
            if len(part) > 0 :
                part = re.sub(ur'(@...|\*|\(.{,2}\)?)', " ", part)
                page.append(part)
        rif.append(page)
    return rif


def save_parsed_text(text):
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": 'Rif on Taanit',
        "versionTitle": "Presburg : A. Schmid, 1842",
        "versionSource": "http://www.worldcat.org/title/perush-radak-al-ha-torah-sefer-bereshit/oclc/867743220",
        "language": "he",
        "text": text,
    }

#    save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/rif_on_taanit.json", 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    Helper.createBookRecord(book_record())
    with open("preprocess_json/rif_on_taanit.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Rif on Taanit", file_text, False)


if __name__ == '__main__':
    Helper.createBookRecord(book_record())
    #text = open_file()
    #parsed = parse(text)
    #save_parsed_text(parsed)
    #run_post_to_api()
