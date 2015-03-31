# -*- coding: utf-8 -*-
__author__ = 'eliav'
import re
import json
import sys
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
import hebrew


def book_record():
      return {
    "title" : "Korban Netanel on Taanit",
    "categories" : [
        "Other",
        "Rosh"
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Korban Netanel on Taanit",
                "primary" : True
            },
            {
                "lang" : "he",
                "text" : 'קרבן נתנאל על מסכת תענית',
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
        "key" : "Korban Netanel on Taanit"
    }
	}


def open_file():
    with open("source/korban_netanel_taanit.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        return ucd_text


def parse(text):
    seifim = re.split('\[\*\]',text)
    netanel =[]
    for i,siman in enumerate(seifim[1:]):
        cut = re.split('@55', siman)
        if len(cut) >1:
            netanel.append("<b> " + re.sub('@[0-9][0-9]',"",cut[0]) + " </b> " + cut[1])
        else:
            netanel.append(cut[0])
        if '@00' in netanel[i]:
            netanel[i] = re.findall('(.*\s)@00.*\s',netanel[i])[0]
        print netanel[i]
    return  netanel


def save_parsed_text(text):
    text_whole = {
        "title": 'Korban Netanel on Taanit',
        "versionTitle": "Vilna, 1842",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "language": "he",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/korban_netanel_on_Taanit.json", 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    Helper.createBookRecord(book_record())
    with open("preprocess_json/korban_netanel_on_Taanit.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Korban Netanel on Taanit", file_text, False)

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