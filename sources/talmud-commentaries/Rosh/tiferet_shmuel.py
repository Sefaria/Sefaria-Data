# -*- coding: utf-8 -*-
__author__ = 'eliav'
import os
import re
import json
import sys
from sefaria.model import *
sys.path.insert(1, '../../genuzot')
import helperFunctions as Helper
import hebrew

masechet = str(sys.argv[1])
if "_" in masechet:
    mas = re.sub("_", " ", masechet)
else:
    mas = masechet
masechet_he = Index().load({"title":mas}).get_title("he")


def book_record(record = "shmuel"):
    if record =="shmuel":
        a = u" תפארת שמואל על " + masechet_he
        b = u"Tiferet Shmuel on " + masechet
    elif record == "yomtov":
        a = u" מעדני יום טוב על " + masechet_he
        b= u"Maadaney Yom Tov on " + masechet
    elif record == "chamudot":
        a = u" דברי חמודות על " + masechet_he
        b= u"Divrey Chamudot on " + masechet
    return {
    "title" : b,
    "categories": [ "Commentary2",
        "Talmud","Tiferet Shmuel"
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : b,
                "primary" : True
            },
            {
                "lang" : "he",
                "text" :a,
                "primary" : True
            }
        ],
        "nodeType" : "JaggedArrayNode",
        "depth" : 1,
        "sectionNames" : [
            "Siman"


        ],
        "addressTypes" : [
           "Integer"
        ],
        "key" : b
    }
	}


def open_file(record = "shmuel"):
    if record == "shmuel":
         b = u"Tiferet_Shmuel_on"
    elif record == "yomtov":
         b= u"Maadaney_Yom_Tov_on"
    elif record == "chamudot":
        b= u"Divrey_Chamudot_on"
    with open("../source/" + b+ "_%s.txt" % masechet, 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        return ucd_text


def open_file1():
    with open("../source/maadaney_yom_tov_on_%s.txt" % masechet, 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        return ucd_text

def open_basic_file():
    with open("../source/Rosh_on_%s.txt" % masechet, 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        return ucd_text


def parse(text):
    seifim = re.split('[\[\(].[\]\)]',text)
    shmuel =[]
    for i,siman in enumerate(seifim[1:]):
        cut = re.split('(?:@55|@33)', siman)
        if len(cut) >1:
            shmuel.append("<b> " +re.sub(ur"@[0-9][0-9]","",cut[0]) + " </b> " + re.sub(ur"@[0-9][0-9]","",cut[1]))
        else:
            shmuel.append(cut[0])
        #if '@00' in shmuel[i]:
         #   shmuel[i] = re.findall('(.*\s)@00.*\s',shmuel[i])[0]
        #print netanel[i]
    return  shmuel


def save_parsed_text(text, record = "shmuel" ):
    if record == "shmuel":
        b = u"Tiferet Shmuel on  " + masechet
        a = u"Tiferet_Shmuel_on"
    elif record == "yomtov":
        b= u"Maadaney Yom Tov on " + masechet
        a = u"Maadaney_Yom_Tov_on"
    elif record == "chamudot":
        a = u"Divrey_Chamudot_on"
        b = u"Divrey Chamudot on " + masechet
    text_whole = {
        "title": b,
        "versionTitle": "Vilna Edition",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "language": "he",
        "text": text,
        "digitizedBySefaria": True,
        "license": "Public Domain",
        "licenseVetted": True,
        "status": "locked",
    }
    #save
    Helper.mkdir_p("../preprocess_json/")
    with open("../preprocess_json/" + a + "_%s.json" % masechet , 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api(record ="shmuel"):
    if record == "shmuel":
         b = u"Tiferet_Shmuel_on"
         a = u"Tiferet Shmuel on "
    elif record == "yomtov":
         b= u"Maadaney_Yom_Tov_on"
         a = u"Maadaney Yom Tov on "
    elif record == "chamudot":
        b = u"Divrey_Chamudot_on"
        a = u"Divrey Chamudot on "
   # Helper.createBookRecord(book_record())
    with open("../preprocess_json/" + b + "_%s.json" % masechet, 'r') as filep:
        file_text = filep.read()
    Helper.postText( a + "%s" % masechet, file_text, False)

if __name__ == '__main__':
    text = open_file()
    basic_text = open_basic_file()
    parsed_text = parse(text)
    Helper.createBookRecord(book_record())
    save_parsed_text(parsed_text)
    run_post_to_api()
    #Helper.postLink(links)
