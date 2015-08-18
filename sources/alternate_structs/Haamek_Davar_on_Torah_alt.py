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
    "title": "Haamek Davar Intro",
    #"titleVariants": [""],
    "sectionNames": ["content"],
    "categories": ["Musar"],
     "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Haamek Davar Intro",
                "primary" : True
            },
            {
                "lang" : "he",
                "text" : u"הקדמת העמק דבר על התורה",
                "primary" : True
            }
        ],
         "nodeType" : "JaggedArrayNode",
        "depth" : 1,
        "addressTypes": ["Integer"],
        "sectionNames" :["content"],
        "key" : "Haamek Davar Intro"
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
            "title": "Haamek Davar Intro",
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
    Helper.postText("Haamek Davar Intro", file_text, False)


def index():
    structs["nodes"].append({
        "titles": [{
                    "lang": "en",
                    "text": "Haamek Davar Intro",
                    "primary": True
                    },
                    {
                    "lang": "he",
                    "text": u"הקדמת העמק דבר על התורה",
                    "primary": True
                    }],
        "nodeType": "ArrayMapNode",
        "includeSections": True,
        "depth": 0,
        "wholeRef": "Haamek Davar Intro"
    })

    pmap = {
        'Genesis': "Bereshit",
        'Exodus': "Shemot",
        'Leviticus': "Vayikra",
        'Numbers': "Bamidbar",
        'Deuteronomy': "Devarim"
    }

    for chumash in ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']:
        structs["nodes"].append({
            "sharedTitle": pmap[chumash],
            "nodeType": "ArrayMapNode",
            "includeSections": True,
            "depth": 0,
            "wholeRef": "Haamek Davar on " + chumash
        })
    root = JaggedArrayNode()
    root.add_title("Haamek Davar Torah", "en", primary=True)
    root.add_title(u"העמק דבר על התורה", "he", primary=True)
    root.key = "Haamek Davar Torah"
    root.depth = 1
    root.sectionNames = ["Chumash"]
    root.addressTypes = ["Integer"]

    root.validate()

    index = {
        "title": "Haamek Davar Torah",
        "categories": ["Musar"],
        "default_struct": "content",
        "alt_structs": {"content": structs},
        "schema": root.serialize()
    }

    createBookRecord(index)


if __name__ == '__main__':
    open_file() #opens file and posts it
    index()
