# -*- coding: utf8 -*-
__author__ = 'eliav'
import re
import json
import sys
from sefaria.model import *

sys.path.insert(1, '../genuzot')
import helperFunctions as Helper


def g_d():
    shraga = TextChunk(Ref("Deuteronomy"),"en","The Rashi chumash by Rabbi Shraga Silverstein").text
    shraga_text = []
    for shrag in shraga:
        shrag_text=[]
        for sra in shrag:
            subed = re.sub("\sG\sd\s", " G-d ",sra)
            subed = re.sub("\[G\sd\s", "[G-d ",subed)
            shrag_text.append(subed)
        shraga_text.append(shrag_text)
    print shraga_text[0][0]
    return shraga_text

def open_file():
    with open("source/shraga_dvarim.txt" , 'r') as filep:
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
        "title": 'Deuteronomy',
        "versionTitle": "The Rashi chumash by Rabbi Shraga Silverstein",
        "versionSource":  "http://www.sefaria.org/shraga-silverstein",
        "language": "en",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Shraga_Silverstein_translation_on_Deuteronomy.json", 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    #Helper.createBookRecord(book_record())
    with open("preprocess_json/Shraga_Silverstein_translation_on_Deuteronomy.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Deuteronomy"  , file_text, False)





if __name__ == '__main__':
    text = open_file()
    parsed = parse(text)
    #print len(parsed)
    #print parsed[0]
    #parsed= g_d()
    save_parsed_text(parsed)
    print parsed[0][0]
    run_post_to_api()
