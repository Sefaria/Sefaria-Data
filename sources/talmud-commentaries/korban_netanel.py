# -*- coding: utf-8 -*-
__author__ = 'eliav'
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

def book_record():
    a = u" קרבן נתנאל על " + masechet_he
    return {
    "title" : "Korban Netanel on %s" % masechet,
    "categories" : [
        "Other",
        "Rosh"
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Korban Netanel on %s" % masechet,
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
        "key" : "Korban Netanel on %s" % masechet
    }
	}


def open_file():
    with open("source/Korban_Netanel_on_%s.txt" % masechet, 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        return ucd_text


def parse(text):
    seifim = re.split('\[\*\]',text)
    netanel =[]
    for i,siman in enumerate(seifim[1:]):
        cut = re.split('(?:@55|@33)', siman)
        if len(cut) >1:
            netanel.append("<b> " + re.sub('@[0-9][0-9]',"",cut[0]) + " </b> " + cut[1])
        else:
            netanel.append(cut[0])
        if '@00' in netanel[i]:
            netanel[i] = re.findall('(.*\s)@00.*\s',netanel[i])[0]
        #print netanel[i]
    return  netanel


def save_parsed_text(text):
    text_whole = {
        "title": 'Korban Netanel on %s' % masechet,
        "versionTitle": "Vilna, 1842",
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
    with open("preprocess_json/korban_netanel_on_%s.json" % masechet , 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    Helper.createBookRecord(book_record())
    with open("preprocess_json/korban_netanel_on_%s.json" % masechet, 'r') as filep:
        file_text = filep.read()
    Helper.postText("Korban Netanel on %s" % masechet, file_text, False)

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