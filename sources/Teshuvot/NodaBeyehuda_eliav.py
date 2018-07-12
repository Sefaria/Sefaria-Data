# -*- coding: utf-8 -*-
import re
import sys
import json
from sefaria.model import *
import sefaria.utils.hebrew
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
from httplib import BadStatusLine

def book_record():
    return {
        "title": 'Noda Byehuda I',
        "titleVariants": [" ", " "],
        "heTitle": 'נודע ביהודע',
        "heTitleVariants" :['שו"ת נודע ביהודה', ' '],
        "sectionNames": ["", ""],
        "categories": ['Responsa'],
    }


def build_index():
    root = SchemaNode()
    root.key = 'Noda Byehuda I'
    root.add_title("Noda Byehuda I", "en", primary=True)
    root.add_title(u"נודע ביהודה", "he", primary=True)
    part1 = JaggedArrayNode()
    part1.key = 'Orach Chaim'
    part1.add_title(u"אורח חיים", "he", primary=True)
    part1.add_title("Orach Chaim", "en", primary=True)
    part1.depth = 2
    part1.sectionNames = ["Teshuva", "seif"]
    part1.addressTypes = ["Integer", "Integer"]

    part2 = JaggedArrayNode()
    part2.key = 'Yoreh De\'ah'
    part2.add_title(u"יורה דעה", "he", primary=True)
    part2.add_title("Yoreh De\'ah", "en", primary=True)
    part2.depth = 2
    part2.sectionNames = ["Teshuva", "seif"]
    part2.addressTypes = ["Integer", "Integer"]

    part3 = JaggedArrayNode()
    part3.key = 'Even HaEzer'
    part3.add_title(u"אבן העזר", "he", primary=True)
    part3.add_title("Even HaEzer", "en", primary=True)
    part3.depth = 2
    part3.sectionNames = ["Teshuva", "seif"]
    part3.addressTypes = ["Integer", "Integer"]

    part4 = JaggedArrayNode()
    part4.key = 'Choshen Mishpat'
    part4.add_title(u"חושן משפט", "he", primary=True)
    part4.add_title("Choshen Mishpat", "en", primary=True)
    part4.depth = 2
    part4.sectionNames = ["Teshuva", "seif"]
    part4.addressTypes = ["Integer", "Integer"]

    root.append(part1)
    root.append(part2)
    root.append(part3)
    root.append(part4)

    root.validate()
    index = {
        "title": "Noda Byehuda I",
        "categories": ["Responsa"],
        "schema": root.serialize()
    }
    return index

def open_file():
    with open("source/TeshuvutNodaBeyehuda.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
    return ucd_text


def parse(text):
    parts = re.split(ur"@99(.*)(?:\n|:)",text)
    noda = []
    for name,part in zip(parts[1::2],parts[0::2]):
        chalakim =[]
        new_numeral = 0
        # Questions begin with:
        # @22 <hebrew number> \n
        # The lines afterward are the body of the question

        # Regular lines often (always?) look like:
        # @11 ... @33 ... \n

        # Questions may have header material in front of them.
        # The header material might include
        # @00 ... \n
        # @77 ... @66 ... \n
        # @88 ... \n

        stuff = re.split(ur"((?:@[087]+.*)\n)*@22([א-ת ]+)\n", part)
<<<<<<< Updated upstream
        pass
        first = re.finditer(ur"(@00.*?)?(@88.*?)?(@77.*?@66.*?)?\n?@22([א-ת ]+)\n(.*?)(?=@[082])", part, flags=re.DOTALL)
=======
        for intro,number,text in zip(stuff[1::3], stuff[2::3], stuff[3::3]):
            teshuva = []
            int =""
            if intro is not None:
                introduction = re.finditer(ur"@[0-9][0-9](.*?)@[0-9][0-9](.*)", intro)
                for segment in introduction:
                    int =int + '<b>' + segment.group(1) + "</b>" + segment.group(2)
                    if len(re.findall(ur"@[0-9][0-9]",int))>0:
                        int = re.sub(ur"@[0-9][0-9]", "",int)
                    #print number
                    teshuva.append(int)
            answer = re.finditer(ur"@[0-9][0-9](.*?)@[0-9][0-9](.*)", text)
            for ans in answer:
                siman ='<b>' + ans.group(1) + "</b>" + ans.group(2)
                if len(re.findall(ur"@[0-9][0-9]",siman))>0:
                        siman = re.sub(ur"@[0-9][0-9]", "",siman)
                teshuva.append(siman)
            chalakim.append(teshuva)
        noda.append(chalakim)
    return noda
        #pass
        #first = re.finditer(ur"(@00.*?)?(@88.*?)?(@77.*?@66.*?)?\n?@22([א-ת ]+)\n(.*?)(?=@[082])", part, flags=re.DOTALL)
>>>>>>> Stashed changes
        #first = re.finditer(ur"(@00.*\n)?(@88.*\n)?(@77.*@66.*)?\n?@22([א-ת][א-ת]?[א-ת]?)(^@[28])*?",part)
        #second = re.finditer(ur"(@00.*\n)?(@88.*\n)?(@77.*@66.*)?\n?@22([א-ת][א-ת]?[א-ת]?)([^a-z]*)",part)

"""
        for fir in  first:
            teshuva = []
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
            shela = fir.group(4).strip()
            print shela
            numeral = sefaria.utils.hebrew.heb_string_to_int(shela)
            if numeral - new_numeral != 1:
                print shela, numeral
            new_numeral = numeral
            noda.append(teshuva)
        #print fir.group(5)
        #print name
    return noda
"""

<<<<<<< Updated upstream
def save_parsed_text(text):
=======
def save_parsed_text(text, chelek):
>>>>>>> Stashed changes
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": 'Noda Byehuda I, ' + chelek,
        "versionTitle": "Noda B'Yehuda, Warsaw 1880",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001983501",
        "language": "he",
        "text": text,
        "status":"locked",
        "digitizedBySefaria" : True,
        "licenseVetted" : True,
        "license" : "Public Domain"
    }
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Noda_Byehuda_I_{}.json".format(chelek), 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api(chelek):
    with open("preprocess_json/Noda_Byehuda_I_{}.json".format(chelek), 'r') as filep:
        file_text = filep.read()
    try:
        Helper.postText("Noda Byehuda I, " + chelek, file_text, False)
    except BadStatusLine as e:
        print e





if __name__ == '__main__':
    text = open_file()
    parsed = parse(text)
<<<<<<< Updated upstream
    pass

    #Helper.createBookRecord(book_record())
    #save_parsed_text(parsed)
    #run_post_to_api()
=======
    print len(parsed)
    for i , foo in enumerate(parsed):
        if len(foo)<1:
            print i
    Helper.createBookRecord(build_index())
    for i, chelek in enumerate( [u"Orach Chaim",u"Yoreh De\'ah", u'Even HaEzer', u"Choshen Mishpat"]):
        save_parsed_text(parsed[i], chelek)
        run_post_to_api(chelek)
        print chelek



>>>>>>> Stashed changes






