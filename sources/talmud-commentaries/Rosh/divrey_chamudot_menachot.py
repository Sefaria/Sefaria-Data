# -*- coding: utf-8 -*-
__author__ = 'eliav'
import urllib2
import urllib
import os
import re
import json
import sys
from sefaria.model import *
sys.path.insert(1, '../../genuzot')
import helperFunctions as Helper
import hebrew
depth = lambda L: isinstance(L, list) and max(map(depth, L))+1
masechet = str(sys.argv[1])
if "_" in masechet:
    mas = re.sub("_", " ", masechet)
else:
    mas = masechet
masechet_he = Index().load({"title":mas}).get_title("he")

partslist = ["Hilchot Sefer Torah" ,
"Hilchot Mezuza",
"Hilchot Tefilin",
"Hilchot Tefilin, Shimoosha Raba",
"Hilchot Tzitzit",
"Hilchot Tzitzit, Making Tzitzit",
"Hilchot Tuma'a",
"Hilchot Chala",
"Hilchot Kilayim",
"Hilchot Orlah"]


def parse(text):
    commentary = []
    for j,part in enumerate(text):
        seifim = re.split('[\[\(]..?.?[\]\)]',part)
        shmuel =[]
        print seifim[0]
        for i,siman in enumerate(seifim[1:]):
            cut = re.split('(?:@55|@33)', siman)
            if len(cut)>2:
                shmuel.append("<b> " + re.sub('@[0-9][0-9]',"",cut[0]) + " </b> " +  re.sub('@[0-9][0-9]',"",cut[1]) + " ".join(cut[2:]))
            elif len(cut) >1:
                shmuel.append("<b> " + re.sub('@[0-9][0-9]',"",cut[0]) + " </b> " +  re.sub('@[0-9][0-9]',"",cut[1]))
            else:
                shmuel.append(cut[0])
        commentary.append(shmuel)
    return commentary


def open_file(record):
    if record == "chamudot":
        with open("../source/Divrey_Chamudot_on_%s.txt" % masechet, 'r') as filep:
            file_text = filep.read()
            ucd_text = unicode(file_text, 'utf-8', errors='ignore').strip()
            #print masechet_he
            return ucd_text


def cut_to_parts(text):
    parts = re.split(ur"@00(.*?)(?=\n)", text)
    divrey =[]
    names_list=[]
    for names, parts in zip(parts[1::2] , parts[2::2]):
        names_list.append(names)
        divrey.append(parts)
    return names_list, divrey


def clean(text):
    tif=[]
    print depth(text)
    for j in text:
        clean_text = re.sub("(?:@|[0-9][0-9]|\[|\*|\]|\(\*\)|[!#%])","", j)
        tif.append(clean_text)
    return tif


def book_record(record = "chamudot"):
    if record =="shmuel":
        a = u" תפארת שמואל על " + masechet_he
        b = u"Tiferet Shmuel on " + masechet
    elif record == "yomtov":
        a = u" מעדני יום טוב על " + masechet_he
        b= u"Maadaney Yom Tov on " + masechet
    elif record == "chamudot":
        a = u" דברי חמודות על " + masechet_he
        b= u"Divrey Chamudot on " + masechet
    root = SchemaNode()
    root.add_title(b, "en", primary=True)
    root.add_title(a, "he", primary=True)
#    root.add_title("Halachot Ketanot laRosh","en", primary= False)
 #   root.add_title(u'הלכות קטנות לרא"ש',"he", primary= False)
    root.key = b

    #sefer torah
    sefer_tora = JaggedArrayNode()
    sefer_tora.add_title("Hilchot Sefer Torah", "en", primary=True)
    sefer_tora.add_title("הלכות ספר תורה", "he", primary=True)
    sefer_tora.key = sefer_tora.primary_title()
    sefer_tora.depth = 1
    sefer_tora.sectionNames = [ "Siman"]
    sefer_tora.addressTypes = ["Integer"]

    #Mezuza
    mezuza = JaggedArrayNode()
    mezuza.add_title(u"הלכות מזוזה", "he", primary=True)
    mezuza.add_title("Hilchot Mezuza", "en", primary=True)
    mezuza.key = mezuza.primary_title()
    mezuza.depth = 1
    mezuza.sectionNames = [ "Siman"]
    mezuza.addressTypes = [ "Integer"]

    tefilin = JaggedArrayNode()
    tefilin.add_title("Hilchot Tefilin", "en", primary=True)
    tefilin.add_title("הלכות תפילין", "he", primary=True)
    tefilin.key = tefilin.primary_title()
    tefilin.depth = 1
    tefilin.sectionNames = [ "Siman"]
    tefilin.addressTypes = [ "Integer"]
    tefilin.key = tefilin.primary_title()

    #shimoosha
    shimoosha = JaggedArrayNode()
    shimoosha.depth = 1
    shimoosha.sectionNames = [ "Siman"]
    shimoosha.addressTypes = [ "Integer"]
    shimoosha.add_title("Hilchot Tefilin, Shimoosha Raba", "en", primary = True)
    shimoosha.add_title("שימושא רבא", "he", primary = True)
    shimoosha.key = shimoosha.primary_title()
    #tzitzit
    maintzitzit = JaggedArrayNode()
    maintzitzit.add_title("Hilchot Tzitzit", "en", primary=True)
    maintzitzit.add_title(ur'הלכות ציצית', "he", primary = True)
    maintzitzit.key = maintzitzit.primary_title()
    maintzitzit.depth = 1
    maintzitzit.sectionNames = [ "Siman"]
    maintzitzit.addressTypes = [ "Integer"]

    tzitzit = JaggedArrayNode()
    tzitzit.add_title("Hilchot Tzitzit, Making Tzitzit", "en", primary=True)
    tzitzit.add_title(ur'עשיית ציצית', "he", primary = True)
    tzitzit.key = tzitzit.primary_title()
    tzitzit.depth = 1
    tzitzit.sectionNames = [ "Siman"]
    tzitzit.addressTypes = [ "Integer"]

    tomaa = JaggedArrayNode()
    tomaa.add_title("Hilchot Tuma'a", "en", primary=True)
    tomaa.add_title(ur'הלכות טומאה', "he", primary = True)
    tomaa.key = tomaa.primary_title()
    tomaa.depth = 1
    tomaa.sectionNames = [ "Siman"]
    tomaa.addressTypes = [ "Integer"]

    chala = JaggedArrayNode()
    chala.add_title("Hilchot Chala", "en", primary=True)
    chala.add_title(ur'הלכות חלה', "he", primary = True)
    chala.key = chala.primary_title()
    chala.depth = 1
    chala.sectionNames = [ "Siman"]
    chala.addressTypes = [ "Integer"]

    chala = JaggedArrayNode()
    chala.add_title("Hilchot Chala", "en", primary=True)
    chala.add_title(ur'הלכות חלה', "he", primary = True)
    chala.key = chala.primary_title()
    chala.depth = 1
    chala.sectionNames = [ "Siman"]
    chala.addressTypes = [ "Integer"]

    kilayim = JaggedArrayNode()
    kilayim.add_title("Hilchot Kilayim", "en", primary=True)
    kilayim.add_title(ur'הלכות כלאים', "he", primary = True)
    kilayim.key = kilayim.primary_title()
    kilayim.depth = 1
    kilayim.sectionNames = [ "Siman"]
    kilayim.addressTypes = [ "Integer"]

    orlah = JaggedArrayNode()
    orlah.add_title("Hilchot Orlah", "en", primary=True)
    orlah.add_title(ur'הלכות ערלה', "he", primary = True)
    orlah.key = orlah.primary_title()
    orlah.depth = 1
    orlah.sectionNames = [ "Siman"]
    orlah.addressTypes = ["Integer"]

    root.append(sefer_tora)
    root.append(mezuza)
    root.append(tefilin)
    root.append(shimoosha)
    root.append(maintzitzit)
    root.append(tzitzit)
    root.append(tomaa)
    root.append(chala)
    root.append(kilayim)
    root.append(orlah)
    root.validate()
    indx = {
    "title": b,
    "categories": [ "Commentary2",
        "Talmud","Divrey Chamudot"
    ],
    "schema": root.serialize()
    }
    return indx


def save_parsed_text(text, record = "shmuel", part="" ):
    if record == "shmuel":
        b = u"Tiferet Shmuel on  " + masechet
        a = u"Tiferet_Shmuel_on"
    elif record == "yomtov":
        b= u"Maadaney Yom Tov on " + masechet
        a = u"Maadaney_Yom_Tov_on"
    elif record == "chamudot":
        a = u"Divrey_Chamudot_on"
        b = u"Divrey Chamudot on " + masechet
    text_whole = {
        "title": b,
        "versionTitle": "Vilna Edition",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "language": "he",
        "text": text,
        "digitizedBySefaria": True,
        "license": "Public Domain",
        "licenseVetted": True,
        "status": "locked",
    }
    #save
    Helper.mkdir_p("../preprocess_json/")
    if part=="":
        with open("../preprocess_json/" + a + "_%s.json" % masechet , 'w') as out:
            json.dump(text_whole, out)
    else:
        with open("../preprocess_json/" + a + "_{}_{}.json".format(masechet, part) , 'w') as out:
            json.dump(text_whole, out)


def run_post_to_api(record , part):
    if record == "shmuel":
         b = u"Tiferet_Shmuel_on"
         a = u"Tiferet Shmuel on "
    elif record == "yomtov":
         b= u"Maadaney_Yom_Tov_on"
         a = u"Maadaney Yom Tov on "
    elif record == "chamudot":
        b = u"Divrey_Chamudot_on"
        a = u"Divrey Chamudot on "
   # Helper.createBookRecord(book_record())
    if part =="":
        with open("../preprocess_json/" + b + "_%s.json" % masechet, 'r') as filep:
            file_text = filep.read()
        Helper.postText( a + "%s" % masechet, file_text, False)
    else:
        #part = re.sub("_"," ",part.strip())
        with open("../preprocess_json/" + b + "_{}_{}.json".format(masechet, part), 'r') as filep:
            file_text = filep.read()
        Helper.postText( a + "{}, {}".format(masechet,part), file_text, False)

if __name__ == '__main__':
    text = open_file("chamudot")
    name ,parts = cut_to_parts(text)
    parsed = parse(parts)

    #for part in parsed:
     #   clean(part)

