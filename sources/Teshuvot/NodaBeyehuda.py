# -*- coding: utf-8 -*-
import re
import sys
import json
from sefaria.model import *
import sefaria.utils.hebrew
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper


def book_record():
    return {
        "title": 'Noda Byehuda',
        "titleVariants": [" ", " "],
        "heTitle": 'נודע ביהודע',
        "heTitleVariants" :['שו"ת נודע ביהודה', ' '],
        "sectionNames": ["", ""],
        "categories": ['Responsa'],
    }


def open_file():
    with open("source/TeshuvutNodaBeyehuda.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
    return ucd_text


def parse(text):
    parts = re.split(ur"@99(.*)?(?:\n|:)",text)
    noda = []
    for name,part in zip(parts[1::2],parts[0::2]):
        new_numeral = 0
        first = re.finditer(ur"(@00.*\n)?(@88.*\n)?(@77.*@66.*)?\n?@22([א-ת][א-ת]?[א-ת]?)(^@[28])*?",part)
        #second = re.finditer(ur"(@00.*\n)?(@88.*\n)?(@77.*@66.*)?\n?@22([א-ת][א-ת]?[א-ת]?)([^a-z]*)",part)
        for fir in  first:
            teshuva =[]
            answer=""
            if fir.group(1) is not None:
                ans =re.sub(ur"@00","", fir.group(1))
                answer = ans + "/n"
            if fir.group(2) is not None:
                ans1 =re.sub(ur"@88","", fir.group(2))
                answer1 = ans1 + "/n"
                answer = answer + answer1
            if fir.group(3) is not None:
                ans2 =re.search(ur"@77(.*)@66(.*)", fir.group(3))
                answer2 = "<b>" + ans2.group(1) + '</b>' + ans2.group(2)
                answer = answer + answer2
            teshuva.append(answer)
            shela = fir.group(4)
            print shela
            numeral = sefaria.utils.hebrew.heb_string_to_int(shela)
            if numeral - new_numeral != 1:
                print shela, numeral
            new_numeral = numeral
        noda.append(teshuva)
        #print fir.group(5)
        #print name
    return noda


def save_parsed_text(text):
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": 'Noda Byehuda',
        "versionTitle": " ",
        "versionSource": " ",
        "language": "he",
        "text": text,
    }
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Noda_Byehuda.json", 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    with open("preprocess_json/Noda_Byehuda.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Noda Byehuda", file_text, False)





if __name__ == '__main__':
    text = open_file()
    parsed =parse(text)
    #Helper.createBookRecord(book_record())
    #save_parsed_text(parsed)
    #run_post_to_api()






