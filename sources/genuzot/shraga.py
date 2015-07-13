# -*- coding: utf8 -*-
__author__ = 'eliav'
import re
import json
import sys
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper

def open_file():
    with open("source/shraga.txt" , 'r') as filep:
        file_text = filep.read()
    ucd_text = unicode(file_text, 'utf-8', errors='ignore').strip()
    return ucd_text


def parse(text):
    cut = re.finditer(ur"([0-9][0-9]?:[0-9][0-9]?)(.*)",text)
    past_perek = 0
    past_pasuk = 0
    beresith =[]
    psk= []
    for match in cut:
        perek_pasuk = match.group(1)
        perek = int(re.split(":", perek_pasuk)[0])
        pasuk = int(re.split(":", perek_pasuk)[1])
        print perek
        content = match.group(2)
        if perek - past_perek > 0:
            beresith.append(psk)
            past_pasuk =0
            past_perek = perek
            psk =[]
        elif past_perek > perek:
            break
        if pasuk > past_pasuk:
            print perek, "passuk" , pasuk
            psk.append(content)
            #print pasuk, past_pasuk
            past_pasuk = pasuk
    beresith.append(psk)

    return  beresith[1:len(beresith)]


def book_record():
    return {
        "title": 'Shraga Silverstein translation',
        "titleVariants": ["shraga silverstein"],
        "heTitle": 'שרגא סילברסטיין',
        "heTitleVariants" :[''],
        "sectionNames": ["", ""],
        "categories": ['Commentary'],
    }


def save_parsed_text(text):
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": 'Genesis',
        "versionTitle": "The Rashi chumash by Rabbi Shraga Silverstein",
        "versionSource":  "http://www.sefaria.org/shraga-silverstein",
        "language": "en",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Shraga_Silverstein_translation_on_Genesis.json", 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    #Helper.createBookRecord(book_record())
    with open("preprocess_json/Shraga_Silverstein_translation_on_Genesis.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Genesis"  , file_text, False)





if __name__ == '__main__':
    text = open_file()
    parsed = parse(text)
    print len(parsed)
    print parsed[0]
    save_parsed_text(parsed)
    run_post_to_api()
