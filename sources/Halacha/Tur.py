# -*- coding: utf-8 -*-
__author__ = 'eliav'
import sys
import json
import re
from sefaria.model import *
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
import hebrew


def book_record():

      return {
      "title" : "Tur, Orach Chaim",
      "categories" : [
      "Halakhah"
      ],
      "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Tur, Orach Chaim",
                "primary" : True
            },
            {
                "lang" : "he",
                "text" : u"טור, אורח חיים",
                "primary" : True
            }
        ],
        "nodeType" : "JaggedArrayNode",
        "depth" : 1,
        "sectionNames" : [
            "siman",
        ],
        "addressTypes" : [
            "Integer"
        ],
        "key" : "Tur, Orach Chaim"
    }
	}


def open_file():
    with open("source/turOC1.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
    return ucd_text


def parse(text):
    older_siman = 0
    tur = []
    hilchos = re.split(ur'@00', text)
    for halacha in hilchos:
        if len(halacha) >0:
            halacha_name = halacha.splitlines()[0]
            print halacha_name
        simanim = re.finditer(ur'(@?[0-9]?[0-9]?@?[0-9]?[0-9]?)@22(.*)@11(.*)',halacha)
        for simans in simanim:
             siman = simans.group(2)
             siman = re.sub(ur'[\(\[].*?[\)\]]',"", siman)
             siman = re.sub(ur'[^\u05d0-\u05ea]',"", siman)
             if len(siman)> 4:
                 print simans.group(2)
                 print simans.group(3)
             roman_siman = hebrew.heb_string_to_int(siman.strip())

             if roman_siman - older_siman > 1:
                 print siman
                 print roman_siman

             older_siman = roman_siman
             tur.append(simans.group(2))
    print len(tur)


def save_parsed_text(parsed_text):
    text_whole = {
        "title": 'Tur, Orach Chaim',
        "versionTitle": "Vilna Edition",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "language": "he",
        "text": parsed_text,
        "digitizedBySefaria": True,
        "license": "Public Domain",
        "licenseVetted": True,
        "status": "locked",
    }
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Tur.json", 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    Helper.createBookRecord(book_record())
    with open("preprocess_json/Tur.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Tur, Orach Chaim", file_text, False)



def build_index():
    root = SchemaNode()
    root.key = 'Tur Orach, Chayyim'
    root.add_title(u"טור אורח חיים", "he", primary=True)
    part1 = SchemaNode()
    part1.key = 'part1'
    part1.add_title(u"חלק א': בית נתיבות", "he", primary=True)
    part1.add_title("Part One, Beit Netivot", "en", primary=True)

    intro = JaggedArrayNode()
    intro.key = 'intro'
    intro.add_title("Introduction", "en", primary=True)
    intro.add_title(u"הקדמה", "he", primary=True)
    intro.depth = 1
    intro.sectionNames = ["Paragraph"]
    intro.addressTypes = ["Integer"]
    part1.append(intro)


    part2 = SchemaNode()
    part2.key = 'part2'
    part2.add_title("Part Two, Beit Moed", "en", primary=True)
    part2.add_title(u"חלק ב': בית מועד", "he", primary=True)

    heb_sections = [u"השער הראשון", u"השער השני", u"השער השלישי", u"השער הרביעי", u"השער החמישי"]
    eng_sections = ["The First Gate", "The Second Gate", "The Third Gate", "The Fourth Gate", "The Fifth Gate"]

    for count, word in enumerate(eng_sections):
        gate1 = JaggedArrayNode()
        gate1.key = 'gate'+str(count)
        gate1.add_title(heb_sections[count], "he", primary=True)
        gate1.add_title(word, "en", primary=True)
        gate1.sectionNames = ["Paragraph"]
        gate1.addressTypes = ["Integer"]
        gate1.depth = 1
        part1.append(gate1)
        part2.append(gate1)


    root.append(part1)
    root.append(part2)



    root.validate()


    index = {
        "title": "Avodat HaKodesh",
        "categories": ["Halakhah"],
        "schema": root.serialize()
    }


  #  post_index(index)



if __name__ == '__main__':
        text = open_file()
        parsed =parse(text)
        save_parsed_text(parsed)
        run_post_to_api()
