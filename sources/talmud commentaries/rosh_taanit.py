# -*- coding: utf-8 -*-
__author__ = 'eliav'
import re
import sys
import json
import urllib2
from fuzzywuzzy import fuzz
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
import hebrew
links = []
log = open('rosh.txt', 'w')

def get_shas():
    url = 'http://' + Helper.server + '/api/texts/Taanit.2a-31a'
    response = urllib2.urlopen(url)
    resp = response.read()
    shas = json.loads(resp)["he"]
    return shas


def matching(tagged, shas, i, j, index, daf, amud, strings=15, ratio = False):
    short = 0
    fuzzed =0
    if len(tagged) >= 15:
                    string = " ".join(tagged[0:strings])
    else:
        short += 1
        string = " ".join(tagged[0:len(tagged)-1])
    string = re.sub(ur'[\[\]\*#@[0-9]', "", string)
    found = 0
    for counter, line in enumerate(shas[index], start = 1):
        if fuzz.partial_ratio(string, line) > 85:
            bingo = counter
            if ratio is True:
                if fuzz.ratio(string, line) > 60:
                    fuzzed +=1
                    found +=1
                    #print "ratio", string, daf, strings, fuzz.ratio(string, line)
            else:
                found +=1
    #if fuzzed > 0:
        #print "fuzzed", fuzzed
    if found < 1 and strings != 0:
        strings -= 1
        matching(tagged, shas, i, j, index, daf, amud, strings)
    elif found > 1:
        if ratio is True:
            error = "found too much, " + str(found) + "," + "on," + str(daf)+ "," + amud + "," + " ".join(tagged[0:15]).encode('utf-8') +"\n"
            log.write(error)
        else:
            matching(tagged, shas, i, j, index, daf,amud,strings, True)

    elif found == 1:
        roash = "Rosh on Taanit." + str(i+1) + "." + str(j+1)
        talmud = "Taanit." + str(daf) + amud + "." + str(bingo)
        links.append(link(talmud, roash))
        succes=  "found" + ", " + string.encode('utf-8') + str(daf)+ " ," + amud + "," + str(strings) +"\n"
        print succes
        #log.write(succes)
    elif strings == 0:
        error = "did not find on daf,"+ str(daf) +"," + amud + "," + " ".join(tagged[0:15]).encode('utf-8') +"\n"
        log.write(error)
        print error


def search(text, shas):
    for i, seif in enumerate(text):
        for j, siman in enumerate(seif):
            if siman.endswith(ur'5 '):
                print "yes"
            linked = re.finditer(ur'@44(.*?)@(?:55|11)(.*?)(?=(@44|$))', siman)
            if '@44' not in siman[0:10] and len(siman) > 8:
                start = re.sub('([\[\*\]]|@..|#)',"",siman)
                start_of_siman = re.split(" ", start)
                matching(start_of_siman, shas, i, j, index, daf, amud)
            for match in linked:
                lookfor = match.group(2)
                tagged = re.split(" ", lookfor.strip())
                daf_amud = re.split(ur' ', match.group(1).strip())
                daf =  hebrew.heb_string_to_int(daf_amud[1])
                amud = daf_amud[2]
                index = ((daf-2)*2)+1
                if amud[2].strip() == ur'א':
                    amud = 'a'
                    index = index - 1
                else:
                    amud = 'b'
                if len(lookfor) < 5:
                    print "short", daf, amud
                    break
                else:
                    matching(tagged, shas, i, j, index, daf, amud)


def link(talmud, roash):
    return {
            "refs": [
               talmud,
                roash ],
            "type": "Rosh in Talmud",
            "auto": True,
            "generated_by": "Rosh_taanit",
            }


def open_file():
    with open("source/rosh_taanit.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        return ucd_text


def book_record():
      return {
    "title" : "Rosh on Taanit",
    "categories" : [
        "Other",
        "Rosh"
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Rosh on Taanit",
                "primary" : True
            },
            {
                "lang" : "he",
                "text" : 'פסקי הרא"ש על תענית',
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
        "key" : "Rosh on Taanit"
    }
	}


def parse(text):
    links_netanel = []
    netanel = 0
    rosh = []
    a = re.split(ur'@22([^@]*)', text)
    for seif, cont in zip(a[1::2], a[2::2]):
        si = []
        if ur'[*]' in seif:
                print seif
                netanel += 1
        #si.append(seif)
        content = re.split('@66', cont)
        seif = re.sub(ur'[\s\[\*\]]',"", seif)
        seif = hebrew.heb_string_to_int(seif.strip())
        for num, co in enumerate(content):
            a = re.findall('\[\*\](.{6})', co)
            for b in a:
                print b
            netanel +=len(a)
            #print seif, num, netanel - len(a), netanel
            #print len(a)
            si.append(co)
        rosh.append(si)
    search(rosh,get_shas(),)
    print netanel
    return rosh


def clean(text):
    rosh = []
    for i, seif in enumerate(text):
        si = []
        for j, siman in enumerate(seif):
            siman = re.sub('@44.*?@(?:55|11)',"",siman)
            siman = re.sub('([\[\*\]]|@..|#)',"",siman)
            #print siman
            si.append(siman)
        rosh.append(si)
    return rosh


def save_parsed_text(text):
    text_whole = {
        "title": 'Rosh on Taanit',
        "versionTitle": "Vilna, 1842",
        "versionSource": "???",
        "language": "he",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Rosh_on_Taanit.json", 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    Helper.createBookRecord(book_record())
    with open("preprocess_json/Rosh_on_Taanit.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Rosh on Taanit", file_text, False)

if __name__ == '__main__':
    text = open_file()
    parsed_text = parse(text)
    upload_text = clean(parsed_text)
    #Helper.createBookRecord(book_record())
    #save_parsed_text(upload_text)
    #run_post_to_api()
#    Helper.postLink(links)
