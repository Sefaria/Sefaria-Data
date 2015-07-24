# -*- coding: utf8 -*-
__author__ = 'eliav'
import re
import json
import sys
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
masechet = str(sys.argv[1])

def open_file():
    with open("source/shraga_{}.txt".format(masechet) , 'r') as filep:
        file_text = filep.read()
    ucd_text = unicode(file_text, 'utf-8', errors='ignore').strip()
    return ucd_text


def parse(text):
    cut = re.finditer(ur"(\n[0-9][0-9]?(:|\.)[0-9][0-9]?\n)(.*)",text)
    past_perek = 0
    past_pasuk = 0
    beresith =[]
    psk= []
    for match in cut:
        perek_pasuk = match.group(1)
        print perek_pasuk
        perek = int(re.split(":|\.", perek_pasuk)[0])
        pasuk = int(re.split(":|\.", perek_pasuk)[1])
        print perek
        content = match.group(3)
        print content
        if perek - past_perek > 0:
            beresith.append(psk)
            past_pasuk =0
            past_perek = perek
            psk =[]
        elif past_perek > perek:
            break
        if pasuk > past_pasuk:
            print perek, "mishna" , pasuk
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
        "title": 'Mishnah'.format(masechet),
        "versionTitle": "The Mishna with Obadiah Bartenura by Rabbi Shraga Silverstein",
        "versionSource":  "http://www.sefaria.org/shraga-silverstein",
        "language": "en",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Shraga_Silverstein_translation_on_{}.json".format(masechet), 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    #Helper.createBookRecord(book_record())
    with open("preprocess_json/Shraga_Silverstein_translation_on_{}.json".format(masechet), 'r') as filep:
        file_text = filep.read()
    Helper.postText("Mishna " + masechet  , file_text, False)





if __name__ == '__main__':
    text = open_file()
    parsed = parse(text)
    print len(parsed)

    print len(parsed[0])
    print len(parsed[1])
    save_parsed_text(parsed)
    run_post_to_api()
