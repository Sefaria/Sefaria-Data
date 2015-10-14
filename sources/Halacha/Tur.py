# -*- coding: utf-8 -*-
__author__ = 'eliav'
import sys
import json
import re
from sefaria.model import *
import bet_yosef
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
import hebrew
links =[]

def addlink( simanspot, sifspot,diburspot, part = "Orach Chaim",commentator = "new Bet Yosef"):
    tur = u"New Tur, " + part+ "." +str(simanspot) + "." + str(str(sifspot))
    commentry = commentator + "." +str(simanspot) +"."+ str(diburspot)

    return {
            "refs": [
               tur,
                commentry ],
            "type": "Commentary",
            "auto": True,
            "generated_by": "Tur",
            }


def compare(text, karo):
    for siman in karo:
        print len(siman)


def build_index():
    root = SchemaNode()
    root.key = 'New Tur'
    root.add_title("New Tur", "en", primary=True)
    root.add_title(u"טור חדש", "he", primary=True)
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
        "title": "New Tur",
        "categories": ["Halakhah"],
        "schema": root.serialize()
    }


    return index


def open_file():
    with open("source/turOC1.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
    return ucd_text


def parse(text):
    older_siman = 0
    arbaturim=[]
    tur = []
    hilchos = re.split(ur'@00', text) #split to names of parts
    for halacha in hilchos:
        if len(halacha) >0:
            halacha_name = halacha.splitlines()[0]
            #print halacha_name #get the name of the part
        simanim = re.finditer(ur'(@?[0-9]?[0-9]?@?[0-9]?[0-9]?)@22(.*)@11(.*)',halacha) #cut the text to simanim, get kletter of siman and tags to commentary
        for simans in simanim:
             localbet_yosef = 0
             siman = simans.group(2)
             siman = re.sub(ur'[\(\[].*?[\)\]]',"", siman)
             siman = re.sub(ur'[^\u05d0-\u05ea]',"", siman)
             if len(siman)> 4:
                 print simans.group(2)
                 print simans.group(3)
             roman_siman = hebrew.heb_string_to_int(siman.strip())
             bold = re.split(ur'@33',simans.group(3))
             if len(bold) ==2:
                 text = "<b>" + bold[0] + "</b>" + bold[1]
             else:
                 text = simans.group(3)
             text1 = re.split(u"(.*?[.:])", text)
             text1 = filter(None, text1)
             #taking care of links
             localbet_yosef += len(re.findall("@66",simans.group(1)))
             if "@66" in simans.group(1):
                 links.append(addlink(len(tur)+1,1, localbet_yosef ))
             localbet_yosef += len(re.findall("@66",simans.group(2)))
             if "@66" in simans.group(2):
                 links.append(addlink(len(tur)+1,1, localbet_yosef ))
             for sif_num,sifs in enumerate(text1, start =1):
                 for a in range(1,len(re.findall("@66", sifs))):
                     links.append(addlink(len(tur)+1,sif_num , a+localbet_yosef ))
             if localbet_yosef - len(karo[len(tur)+1]) != -1:
                #print simans.group(2),roman_siman,  localbet_yosef, len(karo[len(tur)+1])
                pass
             if roman_siman - older_siman > 1:
                 print siman
                 print roman_siman
             older_siman = roman_siman

             tur.append(text1)
    arbaturim.append(tur)
    depth = lambda L: isinstance(L, list) and max(map(depth, L))+1
    print depth(tur)
    return tur


def save_parsed_text(parsed_text):
    text_whole = {
        "title": 'New Tur',
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
    Helper.createBookRecord(build_index())
    with open("preprocess_json/Tur.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("New Tur, Orach Chaim", file_text, False)





if __name__ == '__main__':
    betyosef = bet_yosef.open_file()
    karo = bet_yosef.parse(betyosef)
    #bet_yosef.save_parsed_text(karo)
    #bet_yosef.book_record()
    #bet_yosef.run_post_to_api()
    text = open_file()
    parsed =parse(text)
    #compare(text,karo)
    save_parsed_text(parsed)
    run_post_to_api()
    for link in links:
        Helper.postLink(link)
