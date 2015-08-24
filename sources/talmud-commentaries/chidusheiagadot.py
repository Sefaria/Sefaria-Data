# -*- coding: utf-8 -*-
__author__ = 'eliav'
import re
import json
import sys
from fuzzywuzzy import fuzz
from sefaria.model import *
sys.path.insert(1,'../genuzot')
import helperFunctions as Helper
import hebrew
masechet = str(sys.argv[1])
if "_" in masechet:
    mas = re.sub("_", " ", masechet)
else:
    mas = masechet
masechet_he = Index().load({"title":mas}).get_title("he")
shas = TextChunk(Ref("%s" % masechet), "he").text
links=[]
log = open('logs/maharsha_log_%s.txt' % masechet, 'w')


def open_file():
    with open("source/maharsha_%s.txt" % masechet, 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        return ucd_text


def book_record():
    a= " חידושי אגדות על מסכת " + masechet_he.encode('utf-8')
    return {
    "title" : "Chidushei Agadot on %s" % masechet,
    "categories" : [
        "Other",
        "Maharsha"
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Chidushei Agadot on %s" % masechet,
                "primary" : True
            },
            {
                "lang" : "he",
                "text" : a,
                "primary" : True
            }
        ],
        "nodeType" : "JaggedArrayNode",
        "depth" : 2,
        "sectionNames" : [
            "Daf",
            "Peirush"
        ],
        "addressTypes" : [
           "Talmud",
            "Integer",
        ],
        "key" : "Chidushei Agadot on %s" %masechet
    }
	}


def link(talmud, maharsha):
    return {
            "refs": [
               talmud,
                maharsha ],
            "type": "Commentary",
            "auto": True,
            "generated_by": "Chidushei_Agadot_on_%s" % masechet,
            }


def parse(text):
    agadot=[[],[]]
    old_number = 1
    dappim = re.split(ur'@[0-9][0-9]ח"א([^@]*)', text)
    for daf, content in zip(dappim[1::2],dappim[2::2]):
        same = False
        ab = False
        seifim =[]
        if len(daf.split(" ")) > 4:
            if len(daf.split(" "))>=5:
                string= daf.split(" ")[4]
                #print string
            daf_n = daf.split(" ")[2]
            print daf_n
            amud = daf.split(" ")[3].strip()
            if amud[2].strip()== ur"א":
                amuds = 'a'
            elif amud[2].strip() == ur"ב":
                amuds ='b'
            else:
                print "did it get here", amud
        else:
            continue
        number =  hebrew.heb_string_to_int(daf_n)
        if number - old_number==0:
            same =True
        if number - old_number>1:
            for i in range(1,number-old_number):
                agadot.append([])
                agadot.append([])
        old_number = number
        simanim = re.finditer(ur'(?:@[0-9][0-9]|[0-9])(.*)',content)
        for match in simanim:
            if re.search(ur'[0-9]דף', match.group(0)) is not None:
                print match.group(0)
                break
            siman = match.group(0)
            siman = re.split("@77([^(?:@|[0-9]]*)",siman)
            for simans in siman:
                if simans != "":
                    simanim = re.split('(?:@[0-9][0-9]|[0-9])',simans)
                    if len(simanim[0])>1:
                        simanim_string = "<b>" +string + " " + '</b>'+ simanim[0]
                        seifim.append(simanim_string)
                        if ur'<b>ע"ב' in simanim_string:
                            amuds="b"
                            print simanim_string
                            agadot.append(seifim)
                            seifim=[]
                            seifim.append(simanim_string)
                            ab = True
                    if len(simanim) > 1:
                       for i in range(1,len(simanim)-1,2):
                            simanim_string = ur'<b>' + simanim[i] + " " + ur'</b>' + simanim[i+1]
                            if u'<b>ע"ב' in simanim_string:
                                print daf_n
                                amuds="b"
                                print simanim_string
                                agadot.append(seifim)
                                seifim=[]
                                ab = True
                            if len(simanim_string) > 1:
                                seifim.append(simanim_string)
        if amuds =='b':
            if same is True:
                agadot[len(agadot)-1]=seifim
            else:
                if ab == False:
                    agadot.append([])
                agadot.append(seifim)
        elif amuds == 'a':
            agadot.append(seifim)
            agadot.append([])
        else:
            print"here!!!!!!", amud
    print len(agadot)
    return agadot


def save_parsed_text(text):
    text_whole = {
        "title": 'Chidushei Agadot on %s' %masechet,
        "versionTitle": "Vilna Edition",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "language": "he",
        "text": text,
        }
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Chidushei_Agadot_%s.json" % masechet, 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    with open("preprocess_json/Chidushei_Agadot_%s.json" % masechet, 'r') as filep:
        file_text = filep.read()
    Helper.postText("Chidushei Agadot on %s" % masechet, file_text, False)


def search(text):
    for daf_n, daf in enumerate(text):
        for DH_n,DH in enumerate(daf):
            string =  re.split(ur"כו'", DH)[0]
            if daf_n%2 == 0:
                amud="a"
            else:
                amud ="b"
            if daf_n<len(shas):
                gemara_daf = shas[daf_n]
            string = re.sub(ur'</?b>',"",string)
            match(gemara_daf, string,(daf_n/2)+1, amud, DH_n+1)


def match(gemara_daf, string, daf, amud, DH_n, ratio = 100):
    found = 0
    for line_n,line in enumerate(gemara_daf):
        if string in line or line in string:
            found += 1
            found_daf = daf
            found_line = line_n
        else:
            if fuzz.partial_ratio(string, line) > ratio:
                found += 1
                found_daf = daf
                found_line = line_n
    if found == 1:
        print  daf, amud, DH_n
        gemara = masechet + "." + str(found_daf) + amud + "." + str(found_line+1)
        maharsha = "Chidushei Agadot on %s" % masechet + "." + str(daf) + amud + "." + str(DH_n)
        message = "found!! match for maharsha " + str(daf) + str(amud)+ " " + str(DH_n) + "\n"
        log.write(message)
        links.append(link(gemara, maharsha))
        pass
    elif found ==0 and ratio > 55:
        match(gemara_daf, string,daf, amud, DH_n, ratio-1)
    else:
        if found ==0:
            message = "Did not find match for maharsha " + str(daf) + str(amud)+ " " + str(DH_n) + "\n"
            log.write(message)
        if found>1:
            message = "Did not find match for maharsha " + str(daf)+ str(amud) + " " + str(DH_n) + "\n"
            log.write(message)




if __name__ == '__main__':
    text = open_file()
    parsed_text = parse(text)
    #Helper.createBookRecord(book_record())
    #save_parsed_text(parsed_text)
    #run_post_to_api()
    search(parsed_text)
    Helper.postLink(links)