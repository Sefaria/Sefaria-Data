# -*- coding: utf-8 -*-
__author__ = 'eliav'
import sys
import json
import re
from sefaria.model import *
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
import hebrew


def book_record():
      return {
    "title" : "new Bet Yosef" ,
    "categories" : [
       "Commentary2",
       "Halkhah"
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "new Bet Yosef",
                "primary" : True
            },
            {
                "lang" : "he",
                "text" : u"בית יוסף חדש",
                "primary" : True
            }
        ],
        "nodeType" : "JaggedArrayNode",
        "depth" : 2,
        "sectionNames" : [
            "siman",
            "dibur"
        ],
        "addressTypes" : [
           "Integer",
            "Integer"
        ],
        "key" : "new Bet Yosef"
    }
	}

def open_file():
    with open("source/bet_yosefOC1.txt", 'r') as filep:
        file_text1 = filep.read()
        ucd_text1 = unicode(file_text1, 'utf-8').strip()
    with open("source/bet_yosefOC2.txt", 'r') as filep:
        file_text2 = filep.read()
        ucd_text2 = unicode(file_text2, 'utf-8').strip()
        ucd_text = ucd_text1 +ucd_text2
    return ucd_text


def parse(text):
     old_num =0
     simanim = re.finditer(ur'@22\n*(.*)\n*@11(\n?.*)', text)
     for siman in simanim:
        #print siman.group(1)
        new_num = hebrew.heb_string_to_int(siman.group(1).strip())
        if new_num - old_num !=1:
            print siman.group(1)
            print new_num
        old_num = new_num
     print new_num
     bet_yosef=[]
     simanim = re.split("@22", text)
     for siman in simanim:
         dh = re.split("@66", siman)
         bet_yosef.append(dh)
     print len(bet_yosef)
     print bet_yosef[len(bet_yosef)-1][0]
     return bet_yosef


def save_parsed_text(parsed):
    text_whole = {
    "title": 'new Bet Yosef',
    "versionTitle": "Vilna Edition",
    "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
    "language": "he",
    "text": parsed,
    "digitizedBySefaria": True,
    "license": "Public Domain",
    "licenseVetted": True,
    "status": "locked",
    }
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Bet_Yosef.json", 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    Helper.createBookRecord(book_record())
    with open("preprocess_json/Bet_Yosef.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("new Bet Yosef", file_text, False)


if __name__ == '__main__':
    text = open_file()
    parsed =parse(text)
    save_parsed_text(parsed[1:len(parsed)-1])
    run_post_to_api()


