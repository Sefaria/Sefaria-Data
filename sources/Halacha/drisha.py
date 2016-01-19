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
    root.key = 'Drisha'
    root.add_title("Drisha", "en", primary=True)
    root.add_title(u"דרישה", "he", primary=True)
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
        "title": 'Drisha',
        "categories": ["Commentary2", "Halakhah", "New Tur"],
        "schema": root.serialize()
    }
    return index


def open_file():
    with open("source/drishaOC1.txt", 'r') as filep:
        file_text1 = filep.read()
        ucd_text1 = unicode(file_text1, 'utf-8').strip()
    with open("source/drishaOC2.txt", 'r') as filep:
        file_text2 = filep.read()
        ucd_text2 = unicode(file_text2, 'utf-8').strip()
        ucd_text = ucd_text1 +ucd_text2
    return ucd_text


def parse(text):
     old_num =0
     simanim = re.finditer(ur'@22\n*(.*)\n*@11(\n?.*)', text)
     for siman in simanim:
        si =  siman.group(1)
        print si
        num = re.split(" ", si.strip())[1]
        num=re.sub("'","",num)
        new_num = hebrew.heb_string_to_int(num.strip())
        if new_num - old_num !=1:
            print new_num
        old_num = new_num
     drisha=[]
     simanim = re.split("@22", text)
     for siman in simanim:
         seif =[]
         dh = re.split(ur"\[\S\S?\]]", siman)
         print dh[0]
         i = 1
         for text in dh:
             bolded_dh = re.finditer(ur'@11(.*)@33(.*)',text)
             for bold in bolded_dh:
                #new_dh = "{" + str(i) +"}" + "<b>"  + bold.group(1) + '</b>' + bold.group(2)
                new_dh =  "<b>"  + bold.group(1) + '</b>' + bold.group(2)
                seif.append(new_dh)
                i += 1
         drisha.append(seif)
     print "length drisha", len(drisha)
     #print bet_yosef[len(bet_yosef)-1][0]
     if len(drisha[0])<2:
         return drisha[1:len(drisha)-1]
     else:
        return drisha


def save_parsed_text(parsed):
    text_whole = {
    "title": 'Drisha',
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
    with open("preprocess_json/drisha.json", 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    Helper.createBookRecord(build_index())
    with open("preprocess_json/drisha.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Drisha, Orach Chaim", file_text, False)


if __name__ == '__main__':
    text = open_file()
    parsed =parse(text)

    save_parsed_text(parsed)
    run_post_to_api()


