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



def createBookRecord(book_obj):
    url = 'http://' + server + '/api/index/' + book_obj["title"].replace(" ", "_")
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
        return ucd_text


def index():
    intro = open_file()
    structs["nodes"].append({
        "titles":  [{
                    "lang": "en",
                    "text": " Rashi on Torah",
                    "primary": True
                    },
                    {
                    "lang": "he",
                    "text": 'רש"י על התורה',
                    "primary": True
                    }],
        "nodeType": "ArrayMapNode",
        "includeSections": True,
        "depth": 0,
        "addressTypes": [],
        "sectionNames": [],
        "wholeRef": intro
    })
    for chumash in ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy' ]:
        structs["nodes"].append({
            "sharedTitle": chumash,
            "nodeType": "ArrayMapNode",
            "includeSections": True,
            "depth": 3,
            "addressTypes": ["Integer", "Integer", "Integer"],
            "sectionNames": ["chapter", "verse", "comment" ],
            "wholeRef": Ref("Rashi on " + chumash)
        })
