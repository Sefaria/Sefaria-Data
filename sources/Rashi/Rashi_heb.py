# -*- coding: utf-8 -*-
import re
import sys
from sefaria.model import *
import sefaria.utils.hebrew
import json
from httplib import BadStatusLine
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
import hebrew


def open_file():
    with open("source/Rashi_Nikud.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
    return ucd_text


def parse(text):
    old_perek = 0
    prakim = re.finditer("@(\S\S?\S?)(.*)", text)
    rashi =[]
    for perek in prakim:
        pars =1
        perek_num = perek.group(1)
        perek_roman = hebrew.heb_string_to_int(re.sub("[\(\)]","",perek_num.strip()))
        if perek_roman - old_perek !=1:
            print perek_roman
        old_perek = perek_roman
        psukim = re.split(ur"(\([^\u05E4-\u05E9][^\"\”]?\))", perek.group(2))
        prk = []
        old_pasuk = 0
        #try:
            #print pasuk_num, perek_num
        #except Exception:
         #   print "no dibbur"
        for pasuk in psukim:
            r = re.compile(ur"(\([^\u05E4-\u05E9][^\"\”]?\))")
            if r.match(pasuk):
                psk =[]
                pasuk_num = pasuk
                pasuk_roman = hebrew.heb_string_to_int(re.sub(u'[\(\)]',"",pasuk_num.strip()).strip())

                if pasuk_roman - old_pasuk !=1:
                    for a in range(1, pasuk_roman - old_pasuk):
                        print pasuk_num, perek_num
                        prk.append([])
                old_pasuk = pasuk_roman
            else:
                b = re.split(ur"[\:\.]", pasuk)
                for cut in b:
                    if not sefaria.utils.hebrew.has_cantillation(cut, True):
                        try:
                            psk.append(dibbur)
                        except NameError as e:
                            print "name error"
                        dibbur = "<b>" + cut + '</b>'
                    elif cut!=" " and cut !="":
                        dibbur+=cut
            if pars == 1:
                pars =2
                try:
                    prk.append(filter(None,psk[1:]))
                except NameError as e:
                    print "name error"
            else:
                pars = 1
        del psk
        rashi.append(prk)
        #print rashi[len(rashi)-1]
    return rashi


def save_parsed_text(text):
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": 'Rashi on Genesis',
        "versionTitle": "Pentateuch with Rashi's commentary by M. Rosenbaum and A.M. Silbermann",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001969084",
        "language": "he",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Rashi_on_Genesis.json", 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():

    with open("preprocess_json/Rashi_on_Genesis.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Rashi on Genesis", file_text, False)











if __name__ == '__main__':
    text = open_file()
    parsed = parse(text)
    save_parsed_text(parsed)
    try:
        run_post_to_api()
    except BadStatusLine as e:
        print "bad status line"
    print len(parsed)
    print parsed[1][1][0]