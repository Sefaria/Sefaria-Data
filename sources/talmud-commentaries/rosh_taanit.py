# -*- coding: utf8 -*-
__author__ = 'eliav'
import collections
import os
import re
import sys
import json
import urllib2
from fuzzywuzzy import fuzz
import korban_netanel as nosekelim
from sefaria.model import *
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
import hebrew
masechet = str(sys.argv[1])
if "_" in masechet:
    mas = re.sub("_", " ", masechet)
else:
    mas = masechet
masechet_he = Index().load({"title":mas}).get_title("he")
links = []
log = open('log_%s_rosh.txt' % masechet, 'w')
longlog = open('%s_longlog.txt' % masechet, 'w')


def test_depth(text):
    a= re.findall(ur'@22(.{1,2})',text)
    last_sif = 0
    if len([x for x, y in collections.Counter(a).items() if y > 1]) > 0:
           return False
    return True



def get_shas():
    url_index = 'http://' + Helper.server + '/api/index/' + '%s' % masechet
    response_index = urllib2.urlopen(url_index)
    resp_index = response_index.read()
    last_daf = json.loads(resp_index)["length"]
    amud = "a" if last_daf % 2 == 0 else "b"
    daf = (last_daf / 2) + 1
    last_daf =  str(daf) + amud
    url = 'http://' + Helper.server + '/api/texts/' + '%s' % masechet + '.2a' + '-' + last_daf
    response = urllib2.urlopen(url)
    resp = response.read()
    shas = json.loads(resp)["he"]
    return shas


def matching(tagged, shas, i, j, index, daf, amud, strings=15, ratio = False):
    short = 0
    fuzzed =0
    if len(tagged) >= 15:
                    string = " ".join(tagged[0:strings])
    else:
        short += 1
        string = " ".join(tagged[0:len(tagged)-1])
    print string, daf, amud
    string = re.sub(ur'[\[\]\*#@[0-9]', "", string)
    found = 0
    for counter, line in enumerate(shas[index], start = 1):
        if fuzz.partial_ratio(string, line) > 80:
            bingo = counter
            if ratio is True:
                if fuzz.ratio(string, line) > 60:
                    fuzzed +=1
                    found +=1
                    #print "ratio", string, daf, strings, fuzz.ratio(string, line)
            else:
                found +=1
    #if fuzzed > 0:
        #print "fuzzed", fuzzed
    if found < 1 and strings != 0:
        strings -= 1
        matching(tagged, shas, i, j, index, daf, amud, strings)
    elif found > 1:
        if ratio is True:
            error = "found too much, " + str(found) + "," + "on," + str(daf)+ "," + amud + "," + " ".join(tagged[0:15]).encode('utf-8') +"\n"
            log.write(error)
        else:
            matching(tagged, shas, i, j, index, daf,amud,strings, True)

    elif found == 1:
        roash = "Rosh on %s." % masechet + str(i+1) + "." + str(j+1)
        talmud = "%s." % masechet + str(daf) + amud + "." + str(bingo)
        links.append(link(talmud, roash))
        succes=  "found" + ", " + string.encode('utf-8') + str(daf)+ " ," + amud + "," + str(strings) +"\n"
        print succes
        log.write(succes)
    elif strings == 0:
        error = "did not find on daf,"+ str(daf) +"," + amud + "," + " ".join(tagged[0:15]).encode('utf-8') +"\n"
        log.write(error)
        print error


def search(text, shas):
    for i, seif in enumerate(text):
        for j, siman in enumerate(seif):
            if siman.endswith(ur'5 '):
                print "yes"
            linked = re.finditer(ur'@44(.*?)@(?:55|11)(.*?)(?=(@44|$))', siman)
            if '@44' not in siman[0:10] and len(siman) > 8:
                start = re.sub('([\[\*\]]|@..|#)',"",siman)
                start_of_siman = re.split(" ", start)
                print "start of siman", start_of_siman[0]
                if 'index' in locals():
                 #   print "matching", index
                    if index > len(shas):
                        break

                    matching(start_of_siman, shas, i, j, index, daf, amud)
            for match in linked:
                lookfor = match.group(2)
                tagged = re.split(" ", lookfor.strip())
                daf_amud = re.split(ur' ', match.group(1).strip())
                daf = re.sub(ur'[^א-ת]',"",daf_amud[1])
                daf =  hebrew.heb_string_to_int(daf)
                if daf > len(shas) or len(daf_amud) <= 2:
                    print "daf", daf, "is longer than needs to"
                    break
                else:
                    print daf_amud[0]
                    amud = daf_amud[2]
               # print "amud", amud
                index = ((daf-2)*2)+1
                #if index > len(shas):
                #    break
                if amud[2].strip() == ur'א':
                    amud = 'a'
                    index = index - 1
                else:
                    amud = 'b'
                #print "daf", daf, amud
                if index >= len(shas):
                    print "short", daf, amud, lookfor
                    return
                    #break
                else:
                    print "else"
                    matching(tagged, shas, i, j, index, daf, amud)


def link(talmud, roash):
    return {
            "refs": [
               talmud,
                roash ],
            "type": "Rosh in Talmud",
            "auto": True,
            "generated_by": "Rosh_%s" % masechet,
            }


def open_file():
    with open("source/Rosh_on_%s.txt" % masechet, 'r') as filep:
        file_text = filep.read()
      #  print file_text.decode('utf-8','ignore')
        ucd_text = unicode(file_text, 'utf-8').strip()
        print masechet_he
        return ucd_text


def book_record():
    a = u" פסקי הראש על " + masechet_he
    return {
    "title" : "Rosh on %s" % masechet,
    "categories" : [
        "Other",
        "Rosh"
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Rosh on %s" % masechet,
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
            "Halacha",
            "Siman"
        ],
        "addressTypes" : [
           "Integer",
            "Integer"
        ],
        "key" : "Rosh on %s" % masechet
    }
	}


def parse(text):
    if os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)):
       # print "has korban netanel 2"
        nose_kelim = nosekelim.open_file()
        fixed = nosekelim.parse(nose_kelim)
        links_netanel = []
        netanel = 0
    rosh = []
    a = re.split(ur'@22([^@]*)', text)
    for seif, cont in zip(a[1::2], a[2::2]):
     #   print seif
        si = []
        korban =[]
        if ur'[*]' in seif and os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)) and netanel <= len(fixed):
            korban.append(fixed[netanel])
            #print len(links_netanel)
            roash = "Rosh on %s." % masechet + str(len(links_netanel)) + ".1"
            netanelink = "Korban Netanel on %s." % masechet + str(len(links_netanel)) + ".1"
            links.append(link(netanelink, roash))
            netanel += 1
            #print "netanel one seif", seif, netanel
            #print fixed[netanel]
        content = re.split('@66', cont)
        #seif = re.sub(ur'[\s\[\*\]#%\(\)[0-9]]',"", seif)
        seif = re.sub(ur'[^א-ת]',"", seif)
     #   print "clean seif" + seif
        seif = hebrew.heb_string_to_int(seif.strip())
      #  print seif
        for num, co in enumerate(content):
            a = re.findall('\[\*\](.{6})', co)
            for b in a:
                if os.path.isfile('source/Korban_netanel_on_{}.txt'.format(masechet)) and netanel < len(fixed):
        #            print netanel
         #           print "len fixed", len(fixed)
                    korban.append(fixed[netanel])
                    roash = "Rosh on %s." % masechet + str(len(links_netanel)+1) + "." + str(num+1)
                    netanelink = "Korban Netanel on %s." % masechet + str(len(links_netanel)+1)+ "."+ str(len(korban))
#                    print netanelink, roash
                    links.append(link(netanelink, roash))
                    netanel +=1
                    #print "netanel two seif",seif, netanel
                    #print fixed[netanel]
            si.append(co)
        if os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)):
            #print "ths is korban", korban
            links_netanel.append(korban)
#            if len(links_netanel[len(links_netanel)-1]) > 0:
#                print links_netanel[len(links_netanel)-1][len(links_netanel[len(links_netanel)-1])-1]
        rosh.append(si)

    #print "searching"
    search(rosh,get_shas(),)
    if os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)):
        nosekelim.save_parsed_text(links_netanel)
        nosekelim.run_post_to_api()
    return rosh


def parse1(text):
    if os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)):
       # print "has korban netanel 2"
        nose_kelim = nosekelim.open_file()
        fixed = nosekelim.parse(nose_kelim)
        links_netanel = []
        netanel = 0
    rosh = []
    #chapters =
    a = re.split(ur'@22([^@]*)', text)
    for seif, cont in zip(a[1::2], a[2::2]):
     #   print seif
        si = []
        korban =[]
        if ur'[*]' in seif and os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)) and netanel <= len(fixed):
            korban.append(fixed[netanel])
            #print len(links_netanel)
            roash = "Rosh on %s." % masechet + str(len(links_netanel)) + ".1"
            netanelink = "Korban Netanel on %s." % masechet + str(len(links_netanel)) + ".1"
            links.append(link(netanelink, roash))
            netanel += 1
            #print "netanel one seif", seif, netanel
            #print fixed[netanel]
        content = re.split('@66', cont)
        #seif = re.sub(ur'[\s\[\*\]#%\(\)[0-9]]',"", seif)
        seif = re.sub(ur'[^א-ת]',"", seif)
     #   print "clean seif" + seif
        seif = hebrew.heb_string_to_int(seif.strip())
      #  print seif
        for num, co in enumerate(content):
            a = re.findall('\[\*\](.{6})', co)
            for b in a:
                if os.path.isfile('source/Korban_netanel_on_{}.txt'.format(masechet)) and netanel < len(fixed):
        #            print netanel
         #           print "len fixed", len(fixed)
                    korban.append(fixed[netanel])
                    roash = "Rosh on %s." % masechet + str(len(links_netanel)+1) + "." + str(num+1)
                    netanelink = "Korban Netanel on %s." % masechet + str(len(links_netanel)+1)+ "."+ str(len(korban))
#                    print netanelink, roash
                    links.append(link(netanelink, roash))
                    netanel +=1
                    #print "netanel two seif",seif, netanel
                    #print fixed[netanel]
            si.append(co)
        if os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)):
            #print "ths is korban", korban
            links_netanel.append(korban)
#            if len(links_netanel[len(links_netanel)-1]) > 0:
#                print links_netanel[len(links_netanel)-1][len(links_netanel[len(links_netanel)-1])-1]
        rosh.append(si)

    #print "searching"
    search(rosh,get_shas(),)
    if os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)):
        nosekelim.save_parsed_text(links_netanel)
        nosekelim.run_post_to_api()
    return rosh


def clean(text):
    rosh = []
    for i, seif in enumerate(text):
        si = []
        for j, siman in enumerate(seif):
            siman = re.sub('@44.*?@(?:55|11)',"",siman)
            siman = re.sub('([\[\*\]]|@..|#)',"",siman)
            #print siman
            si.append(siman)
        rosh.append(si)
    return rosh


def save_parsed_text(text):
    text_whole = {
        "title": 'Rosh on %s' % masechet,
        "versionTitle": "Vilna, 1842",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "language": "he",
        "text": text,
        "digitizedBySefaria": True,
        "license": "Public Domain",
        "licenseVetted": True,
        "status": "locked",
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Rosh_on_%s.json" % masechet, 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    Helper.createBookRecord(book_record())
    with open("preprocess_json/Rosh_on_%s.json" % masechet, 'r') as filep:
        file_text = filep.read()
    Helper.postText("Rosh on %s" % masechet, file_text, False)

if __name__ == '__main__':
    if os.path.isfile('source/Korban_Netanel_on_{}.txt'.format(masechet)):
        print "has Korban 1"
        Helper.createBookRecord(nosekelim.book_record())
    text = open_file()
    print masechet
 #   if test_depth(text) == True:
    parsed_text = parse(text)
    upload_text = clean(parsed_text)
    Helper.createBookRecord(book_record())
#    else:
 #       parsed_text = parse1(text)
  #      upload_text = clean1(parsed_text)
#        Helper.createBookRecord(book_record1())
#    parsed_text = parse(text)
    print "cleaning"
#    upload_text = clean(parsed_text)
    Helper.createBookRecord(book_record())
    save_parsed_text(upload_text)
    run_post_to_api()
    Helper.postLink(links)
