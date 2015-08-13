# -*- coding: utf-8 -*-
import json
import urllib
import urllib2
import sys
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper

from sefaria.model import *
apikey = Helper.apikey
server = Helper.server
structs = {}
structs = { "nodes" : [] }


def intro_basic_record():
    return  {
    "title": "Haamek Davar on Tora intro",
    #"titleVariants": [""],
    "sectionNames": ["content"],
    "categories": ["Musar"],
     "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Haamek Davar on Tora intro",
                "primary" : True
            },
            {
                "lang" : "he",
                "text" : "הקדמת העמק דבר על התורה",
                "primary" : True
            }
        ],
         "nodeType" : "JaggedArrayNode",
        "depth" : 1,
        "addressTypes": ["Integer"],
        "sectionNames" :["content"],
        "key" : "Haamek Davar on Tora intro"
    }
        }


def createBookRecord(book_obj):
    url = 'http://' + server + '/api/v2/raw/index/' + book_obj["title"].replace(" ", "_")
    indexJSON = json.dumps(book_obj)
    values = {
        'json': indexJSON,
        'apikey': apikey
    }
    data = urllib.urlencode(values)
    print url, data
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except HTTPError, e:
        print 'Error code: ', e.code


def open_file():
    with open("introduction.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        save_file(ucd_text)


def save_file(intro):
    text_whole = {
            "title": "Haamek Davar on Torah intro",
            "versionTitle": "",
            "versionSource": "",
            "language": "he",
            "text": intro,
        }
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Haamek_Davar_intro.json", 'w') as out:
        json.dump(text_whole, out)
    with open("preprocess_json/Haamek_Davar_intro.json", 'r') as filep:
        file_text = filep.read()
    createBookRecord(intro_basic_record())
    Helper.postText("Haamek Davar on Tora intro", file_text, False)


def index():
    structs["nodes"].append({
        "titles":  [{
                    "lang": "en",
                    "text": "Haamek Davar on Torah",
                    "primary": True
                    },
                    {
                    "lang": "he",
                    "text": ur'העמק דבר על התורה',
                    "primary": True
                    }],
        "nodeType": "ArrayMapNode",
        "includeSections": True,
        "depth": 0,
        "wholeRef": "Haamek Davar on Tora"
    })
    for chumash in ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy' ]:
        structs["nodes"].append({
            "sharedTitle": chumash,
            "nodeType": "ArrayMapNode",
            "includeSections": True,
            "depth": 3,
            "addressTypes": ["Integer"],
            "sectionNames": ["Chumash" ],
            "wholeRef": "Haamek Davar on " + chumash
        })
    root = JaggedArrayNode()
    root.add_title("Haamek Davar on Torah", "en", primary=True)
    root.add_title(u"העמק דבר על התורה", "he", primary=True)
    root.key = "Haamek Davar on Torah"
    root.depth = 1
    root.sectionNames = ["Chumash"]
    root.addressTypes = ["Integer"]

    root.validate()

    index = {
        "title": "Haamek Davar on Tora",
        "titleVariants": ["Haamek Davar on Torah"],
        "categories": ["Commentary"],
        "default_struct": "content",
        "alt_structs": {"content": structs},
        "schema": root.serialize()
    }

    createBookRecord(index)


if __name__ == '__main__':
    open_file() #opens file and posts it
    index()
