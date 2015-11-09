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
    with open("source/Rashi_Nikud_eng.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
    return ucd_text


def save_parsed_text(text):
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": 'Rashi on Genesis',
        "versionTitle": "Pentateuch with Rashi's commentary by M. Rosenbaum and A.M. Silbermann",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001969084",
        "language": "en",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/en_Rashi_on_Genesis.json", 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():

    with open("preprocess_json/en_Rashi_on_Genesis.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Rashi on Genesis", file_text, False)


def parse(text):
    old_perek = 0
    prakim = re.finditer("@(\S\S?\S?)(.*)", text)
    rashi =[]
    for perek in prakim:
        pars =1
        perek_num = int(re.sub(ur"\.","",perek.group(1)))
        if perek_num - old_perek !=1:
            print perek_num
        old_perek = perek_num
        psukim = re.split(ur"(\([0-9][^\"\”]?\))", perek.group(2))
        prk = []
        old_pasuk = 0
        for pasuk in psukim:
            r = re.compile(ur"(\([0-9][^a-z]?\))")
            if r.match(pasuk):
                psk =[]
                pasuk_num = int(re.sub(ur"[\(\)]","",pasuk))
                if pasuk_num - old_pasuk !=1:
                    for a in range(1, pasuk_num - old_pasuk):
                        prk.append([])
                old_pasuk = pasuk_num
            else:
                b = re.split(ur"(?:^|\.)(?![^(]*\))([^0-9]*?)[-—]", pasuk)

                #b = re.split(ur"(?:^|\.)([^0-9]*?)[-—]", pasuk)

                for cut in b:
                    #if len(re.findall(ur'[a-z]', cut))<=35  and len(cut) > 4:
                    if len(re.findall("\(", cut)) == len(re.findall("\)", cut)) and len(re.findall(ur'[a-z]', cut))<=40  and len(cut) > 4:
                    #if not ((ur"\(" in cut and not ur"\)" in cut) or (ur"\)" in cut and not ur"\(" in cut )) and len(re.findall(ur'[a-z]', cut))<=35  and len(cut) > 6:
                    #if len(re.findall(ur'[a-z]', cut))<=35 and len(re.findall(ur'\S', cut))>= 5 and len(cut) > 0:
                    #if not ((ur"\(" in cut and not ur"\)" in cut) or (ur"\)" in cut and not ur"(")) and len(cut)>5:

                       try:
                            dibbur = dibbur + ":"
                            psk.append(dibbur)
                       except NameError as e:
                            print "name error"
                       dibbur = "<b>" + cut + "-" + '</b>'
                    elif cut !=" ":
                        try:
                            dibbur+=cut
                        except Exception:
                            pass
                try:
                    dibbur = dibbur + ":"
                    psk.append(dibbur)
                except Exception:
                    print "a"
            if pars == 1:
                pars =2
                try:
                    prk.append(filter(None,psk[1:]))
                except NameError as e:
                    print "name error"
            else:
                pars = 1
        #psk.append(dibbur)
        #prk.append(psk)
        del psk
        rashi.append(prk)
    return rashi

if __name__ == '__main__':
    text = open_file()
    parsed = parse(text)
    print len(parsed)
    save_parsed_text(parsed)
    try:
        run_post_to_api()
    except BadStatusLine as e:
        print "bad status line " + e
    print len(parsed)
    print parsed[0][0][1]