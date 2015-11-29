# -*- coding: utf-8 -*-
import re
import sys
import json
from sefaria.model import *
import sefaria.utils.hebrew
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
from httplib import BadStatusLine


def addlink(key, part,  i):
    key = u"Terumat HaDeshen, " + key + "." + str(i)
    main = u"Terumat HaDeshen, " + part + "." + str(i)
    return {
            "refs": [
                key,
                main ],
            "type": "Commentary",
            "auto": True,
            "generated_by": "Terumat_HaDeshen",
            }


def build_index():
    root = SchemaNode()
    root.key = 'Terumat HaDeshen'
    root.add_title("Terumat HaDeshen", "en", primary=True)
    root.add_title(u"תרומת הדשן", "he", primary=True)
    part1 = JaggedArrayNode()
    part1.key = 'Key part I'
    part1.add_title(u"מפתחות לחלק ראשון", "he", primary=True)
    part1.add_title("Key part I", "en", primary=True)
    part1.depth = 1
    part1.sectionNames = ["Siman"]
    part1.addressTypes = ["Integer"]

    part2 = JaggedArrayNode()
    part2.key = 'Part I'
    part2.add_title(u"חלק א'", "he", primary=True)
    part2.add_title("Part I", "en", primary=True)
    part2.depth = 2
    part2.sectionNames = ["Siman", "seif"]
    part2.addressTypes = ["Integer", "Integer"]

    part3 = JaggedArrayNode()
    part3.key = 'Key part II'
    part3.add_title(u"מפתחות לחלק שני", "he", primary=True)
    part3.add_title("Key part II", "en", primary=True)
    part3.depth = 1
    part3.sectionNames = ["Siman"]
    part3.addressTypes = ["Integer"]

    part4 = JaggedArrayNode()
    part4.key = 'Part II'
    part4.add_title(u"חלק ב'", "he", primary=True)
    part4.add_title("Part II", "en", primary=True)
    part4.depth = 2
    part4.sectionNames = ["Siman", "seif"]
    part4.addressTypes = ["Integer", "Integer"]

    root.append(part1)
    root.append(part2)
    root.append(part3)
    root.append(part4)

    root.validate()
    index = {
        "title": "Terumat HaDeshen",
        "categories": ["Responsa"],
        "schema": root.serialize()
    }
    return index


def save_parsed_text(text, chelek):
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": 'Terumat HaDeshen, ' + chelek,
        "versionTitle": "1",
        "versionSource": " ",
        "language": "he",
        "text": text,
        "status":"locked",
        "digitizedBySefaria" : True,
        "licenseVetted" : True,
        "license" : "Public Domain"
    }
    Helper.mkdir_p("preprocess_json/")
    chelek = re.sub(" ", "_", chelek.strip())
    with open("preprocess_json/Terumat_HaDeshen_{}.json".format(chelek), 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api(chelek):
    chelek1 = re.sub(" ", "_", chelek.strip())
    with open("preprocess_json/Terumat_HaDeshen_{}.json".format(chelek1), 'r') as filep:
        file_text = filep.read()
    try:
        Helper.postText("Terumat HaDeshen, " + chelek, file_text, False)
    except BadStatusLine as e:
        print e


def open_file():
    with open("source/TerumatHadeshen.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
    return ucd_text


def parse(text):
    a =  re.finditer(ur"@00(.*?)@11(.*?)@33",text,re.DOTALL)
    for din in a:
        if len(din.group(1).strip()) > 0:
            #print din.group(1).strip()
            pass
        if len(din.group(2).strip()) > 0:
            #print din.group(2).strip()
            pass
    cheleks = re.split(ur'(@11א @33)',text)
    partI = cheleks[0] + cheleks[1] +cheleks[2]
    partII = cheleks[3] + cheleks[4]
    cheleckI = re.split(ur"(@11שאלה א @33)",partI)
    keyI = cheleckI[0]
    terumathadeshenI = cheleckI[1] + cheleckI[2]
    cheleckII =re.split(ur"(@11סימן א @33)",partII)
    keyII = cheleckII[0]
    terumathadeshenII = cheleckII[1] + cheleckII[2]
    simanim = re.finditer(ur"@11([u'\u05d0-\u05ea'][u'\u05d0-\u05ea']?[u'\u05d0-\u05ea']?\s?)@33(.*)?",keyI)
    old_num = 0
    tdkeyone =[]
    for siman in simanim:
        #print siman.group(1)
        roman= sefaria.utils.hebrew.heb_string_to_int(siman.group(1).strip())
        if roman-old_num !=1:
            for i in range(1,roman-old_num):
                tdkeyone.append("")
        old_num=roman
        siman_key = "<b>" + siman.group(1) + '</b>' + siman.group(2)
        tdkeyone.append(siman_key)
    #save_parsed_text(tdkeyone, "Key part I")
    #run_post_to_api("Key part I")
    tdone=[]
    seifim = re.split(ur"@11(שאלה\s?[u'\u05d0-\u05ea'][u'\u05d0-\u05ea']?[u'\u05d0-\u05ea']?\s?)@33", partI )
    for num, seif in zip(seifim[1::2],seifim[2::2]):
        sh =[]
        #ans =  re.split(ur"@11\s?(תשובה\s?)?@33",seif)
        ans =  re.split(ur"@11",seif)
        for eoq, answer in zip(ans[0::2], ans[1::2]):
            a = re.findall(ur"@00(.*?)\n",answer)
            answer = re.sub(ur"@00(.*?)\n", " ", answer )
            if len(a) > 0:
                for b in a:
                    #print b
                    pass
            sheela = '<b>' + num + '</b>' + eoq
            tuva = re.split(ur"@33",answer)
            if len(tuva) > 1:
                tshuva = '<b>' + tuva[0] + '</b>' + tuva[1]
            else:
                tshuva = tuva[0]
        sh.append(sheela)
        sh.append(tshuva)
        tdone.append(sh)
    #print len(tdone)
    #save_parsed_text(tdone, "Part I")
    #run_post_to_api("Part I")
    for i,k in enumerate(tdkeyone):
        #Helper.postLink(addlink("Key part I", "Part I",i))
        pass
    simanimI = re.finditer(ur"@11([u'\u05d0-\u05ea'][u'\u05d0-\u05ea']?[u'\u05d0-\u05ea']?\s?)@33(.*)?",keyII)
    old_num = 0
    tdkeytwo =[]
    for simanI in simanimI:
        #print simanI.group(1)
        romanI= sefaria.utils.hebrew.heb_string_to_int(simanI.group(1).strip())
        if romanI-old_num !=1:
            #print simanI.group(1)
            for i in range(1,romanI-old_num):
                tdkeytwo.append("")
        old_num=romanI
        simanI_key = "<b>" + simanI.group(1) + '</b>' + simanI.group(2)
        tdkeytwo.append(simanI_key)
    #save_parsed_text(tdkeytwo, "Key part II")
    #run_post_to_api("Key part II")
    tdtwo=[]
    seifimI = re.split(ur"@11(סימן\s?[u'\u05d0-\u05ea'][u'\u05d0-\u05ea']?[u'\u05d0-\u05ea']?\s?)@33", partII )
    for ansI, seifI in zip(seifimI[1::2], seifimI[2::2]):
        #print ansI.strip().split(" ")[1]
        teshuvaI = "<b>" + ansI + "</b>" +seifI
        teshuvaI = re.sub(ur"@00(.*?)\n","",teshuvaI)
        tdtwo.append([teshuvaI])
    save_parsed_text(tdtwo, "Part II")
    run_post_to_api("Part II")
    for i,k in enumerate(tdkeytwo):
        #Helper.postLink(addlink("Key part II", "Part II",i))
        pass




if __name__ == '__main__':
    text = open_file()
    #Helper.createBookRecord(build_index())
    parsed = parse(text)

   # print len(parsed)
    #for i , foo in enumerate(parsed):
     #   if len(foo)<1:
      #      print i
    #Helper.createBookRecord(build_index())
    #for i, chelek in enumerate( [u"Orach Chaim",u"Yoreh De\'ah", u'Even HaEzer', u"Choshen Mishpat"]):
     #   save_parsed_text(parsed[i], chelek)
      #  run_post_to_api(chelek)
       # print chelek
