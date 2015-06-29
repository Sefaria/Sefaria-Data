# -*- coding: utf-8 -*-
__author__ = 'eliav'
import os
import re
import json
import sys
import rosh_taanit
from sefaria.model import *
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
import hebrew

masechet = rosh_taanit.masechet
if "_" in masechet:
    mas = re.sub("_", " ", masechet)
else:
    mas = masechet
masechet_he = Index().load({"title":mas}).get_title("he")

def book_record(commentator):
    if commentator == "Korban Netanel":
        a = u" קרבן נתנאל על " + masechet_he
        b = u"Korban Netanel on " + masechet
    if commentator == "Pilpula Charifta":
        b = u"Pilpula Charifta on " + masechet
        a = u" פילפולא חריפתא על " + masechet_he
    return {
    "title" : b,
    "categories" : [
       "Commentary2",
        "Talmud",
        "Bavli",
        Index().load({"title":masechet}).categories[2],
         "%s" % masechet
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
        "depth" : 2,
        "sectionNames" : [
            "Seif",
            "siman"

        ],
        "addressTypes" : [
           "Integer",
           "Integer"
        ],
        "key" : b
    }
	}


def open_file():
    if os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)):
        commentator = "Korban_Netanel_on"
    if os.path.isfile('source/PilPula_Charifta_on_{}.txt'.format(masechet)):
         commentator = "Pilpula_Charifta_on"
    with open("source/"+ commentator +"_%s.txt" % masechet, 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        return ucd_text


def parse(text):
    seifim = re.split('\[\*\]',text)
    netanel =[]
    for i,siman in enumerate(seifim[1:]):
        cut = re.split('(?:@55|@33)', siman)
        if len(cut) >1:
            netanel.append("<b> " + re.sub('@[0-9][0-9]',"",cut[0]) + " </b> " + re.sub('@[0-9][0-9]'," ", cut[1]))
        else:
            netanel.append(re.sub(ur"[\@[0-9][0-9]"," ",cut[0]))
 #       if '@00' in netanel[i]:
  #          netanel[i] = re.findall('(.*\s)@00.*\s',netanel[i])[0]
        #print netanel[i]
    return  netanel


def save_parsed_text(text, commentator):
    print commentator
    if "Korban Netanel" in commentator:
        a = u" קרבן נתנאל על " + masechet_he
        b = u"Korban Netanel on " + masechet
    if "Pilpula Charifta" in commentator:
        b = u"Pilpula Charifta on " + masechet
        a = u" פילפולא חריפתא על " + masechet_he
    text_whole = {
        "title": b + masechet,
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
    Helper.mkdir_p("preprocess_json/")
    saved_commetator = re.sub(" ", "_", commentator.strip())
    with open("preprocess_json/"+saved_commetator +"_%s.json" % masechet , 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api(commentator):
    saved_commetator = re.sub(" ", "_", commentator.strip())
   # Helper.createBookRecord(book_record())
    with open("preprocess_json/" + saved_commetator +"_%s.json" % masechet, 'r') as filep:
        file_text = filep.read()
    Helper.postText( commentator + "on %s" % masechet, file_text, False)

if __name__ == '__main__':
    text = open_file()
    parsed_text = parse(text)
    #Helper.createBookRecord(book_record())
    #save_parsed_text(parsed_text)
    #run_post_to_api()
    #Helper.postLink(links)
    print parsed_text[159]
    print parsed_text[160]
    print parsed_text[161]