# -*- coding: utf-8 -*-
__author__ = 'eliav'
import sys
import json
import re
from sefaria.model import *
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
import hebrew


def build_index():
    root = SchemaNode()
    root.key = 'Bayit Chadash'
    root.add_title("Bayit Chadash", "en", primary=True)
    root.add_title(u"ב\"ח", "he", primary=True)
    part1 = JaggedArrayNode()
    part1.key = 'Orach Chaim'
    part1.add_title(u"אורח חיים", "he", primary=True)
    part1.add_title("Orach Chaim", "en", primary=True)
    part1.depth = 2
    part1.sectionNames = ["siman", "seif"]
    part1.addressTypes = ["Integer", "Integer"]

    part2 = JaggedArrayNode()
    part2.key = 'Yoreh De\'ah'
    part2.add_title(u"יורה דעה", "he", primary=True)
    part2.add_title("Yoreh De\'ah", "en", primary=True)
    part2.depth = 2
    part2.sectionNames = ["siman", "seif"]
    part2.addressTypes = ["Integer", "Integer"]

    part3 = JaggedArrayNode()
    part3.key = 'Even HaEzer'
    part3.add_title(u"אבן העזר", "he", primary=True)
    part3.add_title("Even HaEzer", "en", primary=True)
    part3.depth = 2
    part3.sectionNames = ["siman", "seif"]
    part3.addressTypes = ["Integer", "Integer"]

    part4 = JaggedArrayNode()
    part4.key = 'Choshen Mishpat'
    part4.add_title(u"חושן משפט", "he", primary=True)
    part4.add_title("Choshen Mishpat", "en", primary=True)
    part4.depth = 2
    part4.sectionNames = ["siman", "seif"]
    part4.addressTypes = ["Integer", "Integer"]

    root.append(part1)
    root.append(part2)
    root.append(part3)
    root.append(part4)

    root.validate()


    index = {
        "title": 'Bayit Chadash',
        "categories": ["Commentary2", "Halakhah", "New Tur"],
        "schema": root.serialize()
    }
    return index


def open_file():
    with open("source/bachOC1.txt", 'r') as filep:
        file_text1 = filep.read()
        ucd_text1 = unicode(file_text1, 'utf-8').strip()
    with open("source/bachOC2.txt", 'r') as filep:
        file_text2 = filep.read()
        ucd_text2 = unicode(file_text2, 'utf-8').strip()
        ucd_text = ucd_text1 +ucd_text2
    return ucd_text


def parse(text):
    old_num =0
    dibbur =""
    #simanim = re.finditer(ur'(@[0-9][0-9])\n?(@[0-9][0-9])(.*\n*)', text)
    simanim = re.split("@77",text)
    bayit_chadash = []
    perek =[]
    i=1
    for siman in simanim:
        simans = re.finditer("@11(.*)@33(.*)",siman)

        for s in simans:
            dibbur ="(" + str(i) + ")" +  "<b>" + s.group(1) + '</b>'+ s.group(2)
            print i
            i = i +1
        if "@22" not in siman:

            perek.append(dibbur)
        elif "@22" in siman:
             #i = 1
             num = re.findall("@22(.*)",siman) [0]
             new_num = hebrew.heb_string_to_int(num.strip())
             #print new_num
             if new_num - old_num != 1:
                 for k in range(1,new_num - old_num):
                    bayit_chadash.append([])
             old_num= new_num
             bayit_chadash.append(perek)
             perek =[]

             perek.append(dibbur)
             i=1
    bayit_chadash.append(perek)
    #print len(bayit_chadash)
    return  bayit_chadash[1:len(bayit_chadash)]


def save_parsed_text(parsed):
    text_whole = {
    "title": 'Bayit Chadash',
    "versionTitle": "Vilna 1924",
    "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001935970",
    "language": "he",
    "text": parsed,
    "digitizedBySefaria": True,
    "license": "Public Domain",
    "licenseVetted": True,
    "status": "locked",
    }
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Bayit_Chadash.json", 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    Helper.createBookRecord(build_index())
    with open("preprocess_json/Bayit_Chadash.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Bayit Chadash, Orach Chaim", file_text, False)




if __name__ == '__main__':
    text = open_file()
    parsed =parse(text)
    save_parsed_text(parsed)
    run_post_to_api()