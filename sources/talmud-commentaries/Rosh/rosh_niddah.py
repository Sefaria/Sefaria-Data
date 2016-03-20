# -*- coding: utf8 -*-
__author__ = 'eliav'
from sefaria.model import *
import os
import korban_netanel as nosekelim
import complex_tiferet_shmuel
import tiferet_shmuel
import re
import json
import urllib2
import urllib
import sys
from HTMLParser import HTMLParser
from fuzzywuzzy import fuzz
sys.path.insert(1, '../../genuzot')
import helperFunctions as Helper
import hebrew
sys.path.insert(0, '../../Match/')
from match import Match
misparim = {'ראשון':1, 'שני':2, 'שלישי':3, 'רביעי':4, 'חמישי':5, 'שישי':6,'ששי':6, 'שביעי':7,'שמיני':8, 'תשיעי':9,'עשירי':10, 'אחד עשר':11}
links = []
masechet = "Niddah"
masechet_he = ur"נידה"
deploy =True
shas = TextChunk(Ref("%s" % masechet), "he").text
log =open("../../../Match Logs/Talmud/{}/log_rosh_on_{}.txt".format(masechet,masechet),"w")


def link_tiferet_shmuel1(parsed_text, part):
    shmuellinks = []
    count = 0
    file = complex_tiferet_shmuel.open_file(record = "chamudot",part=part)
    parsed = complex_tiferet_shmuel.parse(file)
    clean = complex_tiferet_shmuel.clean(parsed)
    complex_tiferet_shmuel.save_parsed_text(clean,record = "chamudot", part=part)
    complex_tiferet_shmuel.run_post_to_api(record = "chamudot", part=part)
    for k, perek in enumerate(parsed_text):
            for j, siman in enumerate(perek):
                #if re.match('\(.\)', siman):
                 if ur'(*)' in siman:
                    #print ur"הגעתי לכאן!"
                    a = re.findall('\(\*\)', siman)
                    part = re.sub("_"," ",part.strip())
                    for b in a:
                        #print siman
                        count +=1
                        roash = "Rosh on %s, " % masechet + part + "." + str(k+1) +  "." + str(j+1)
                        shmuel = "Divrey Chamudot on " + masechet + "," + " " + part +  "." + str(count)
                        shmuellinks.append(link(roash, shmuel))
                        #print count
                        #print roash, shmuel
    Helper.postLink(shmuellinks)


def link_tiferet_shmuel(parsed_text):
    shmuellinks = []
    count = 0
    file = complex_tiferet_shmuel.open_file(record = "chamudot")
    parsed = complex_tiferet_shmuel.parse(file)
    cleantext = complex_tiferet_shmuel.clean(parsed)
    complex_tiferet_shmuel.book_record(record = "chamudot")
    complex_tiferet_shmuel.save_parsed_text(cleantext, record = "chamudot")
    complex_tiferet_shmuel.run_post_to_api(record = "chamudot")
    for k, perek in enumerate(parsed_text):
        for i, seif in enumerate(perek):
            for j, siman in enumerate(seif):
                #if re.match('\(.\)', siman):
                 if ur'(*)' in siman:
                    #print ur"הגעתי לכאן!"
                    a = re.findall('\(\*\)', siman)
                    for b in a:
                        #print siman
                        count +=1
                        roash = "Rosh on %s." % masechet + str(k+1) + "." + str(i+1) + "." + str(j+1)
                        shmuel = "Divrey Chamudot on " + masechet + "." + str(count)
                        shmuellinks.append(link(roash, shmuel))
                        #print count
                        #print roash, shmuel
    Helper.postLink(shmuellinks)


def search2(parsed):
    for i,perek in enumerate(parsed):
       for j, pasuk in enumerate(perek):
           for k, seif in enumerate(pasuk):
               found =  re.finditer(ur'@44\[דף(.*?)\](.*?)\.', seif)
               for find in found:
                   daf = find.group(1)
                   text =  find.group(2)
                   if daf.strip().split(" ")[1] == u'ע"א':
                       amud = 'a'
                   elif daf.strip().split(" ")[1] == u'ע"ב':
                       amud = 'b'

                   new_daf = daf.strip().split(" ")[0]
                   try:
                       daf_num = hebrew.heb_string_to_int(new_daf)
                       #print str(daf_num) + amud
                       found = matchobj(daf_num, amud, text)
                       line = found[1][0]
                       if line >0:
                        #print "Rosh on {}".format(masechet), daf_num, amud, found[1][0], str(i+1), ",", str(j+1) + ",", str(k+1)
                        talmud = "{}".format(masechet) +  "." + str(daf_num) + amud + "." + str(line)
                        roash = "Rosh on {}".format(masechet) +"." + str(i+1) + "." + str(j+1) + "." + str(k+1)

                        links.append(link(talmud,roash))
                   except KeyError:
                       pass


def link(talmud, roash):
    return {
            "refs": [
               talmud,
                roash ],
            "type": "commentary",
            "auto": True,
            "generated_by": "Rosh_%s" % masechet,
            }


def postdText(ref1, text, serializeText = True):
    if serializeText:
        textJSON = json.dumps(text)
    else:
        textJSON = text
    ref1 = ref1.replace(" ", "_")
    url = 'http://' + Helper.server + '/api/texts/{}?index_after=0'.format(ref1)
    print url
    values = {
        'json': textJSON,
        'apikey': Helper.apikey
    }
    print values
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except urllib2.HTTPError, e:
        print 'Error code: ', e.code
        print e.read()


def postText(ref1, ref2, text, serializeText = True):
    if serializeText:
        textJSON = json.dumps(text)
    else:
        textJSON = text
    ref1 = ref1.replace(" ", "_")
    ref2 = ref2.replace(" ", "_")
    url = 'http://' + Helper.server + '/api/texts/{}_{}?index_after=0'.format(ref1,ref2)
    print url
    values = {
        'json': textJSON,
        'apikey': Helper.apikey
    }
    print values
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except urllib2.HTTPError, e:
        print 'Error code: ', e.code
        print e.read()


def open_file():
    with open("../source/Rosh_on_%s.txt" % masechet, 'r') as filep:
        file_text = filep.read()
      #  print file_text.decode('utf-8','ignore')
        ucd_text = unicode(file_text, 'utf-8', errors='ignore').strip()
        #print masechet_he
        return ucd_text


def book_record1():
    b = u"Rosh on %s" % masechet
    a = u"פסקי הראש על" + u" " + masechet_he
    root = SchemaNode()
    root.add_title(b, "en", primary=True)
    root.add_title(a, "he", primary=True)
    root.key = b
    prakim = JaggedArrayNode()
    prakim.default = True
    prakim.depth = 3
    prakim.sectionNames = ["Perek", "Halacha", "siman"]
    prakim.addressTypes = ["Integer", "Integer", "Integer"]
    prakim.key = "default"
    kilaim = JaggedArrayNode()
    kilaim.add_title(u"הלכות כלאי בגדים", "he", primary=True)
    kilaim.add_title("Hilchot Kilay Begadim", "en", primary=True)
    kilaim.key = "Hilchot Kilay Begadim"
    kilaim.depth = 2
    kilaim.sectionNames = ["Seif", "siman"]
    kilaim.addressTypes = ["Integer","Integer"]
    mikva = JaggedArrayNode()
    mikva.add_title("Hilchot Mikvaot", "en", primary=True)
    mikva.add_title(ur'הלכות מקוואות', "he", primary = True)
    mikva.key = "Hilchot Mikvaot"
    mikva.depth = 2
    mikva.sectionNames = ["Seif","Siman"]
    mikva.addressTypes = ["Integer", "Integer"]

    root.append(prakim)
    root.append(kilaim)
    root.append(mikva)
    root.validate()
    indx = {
    "title": b,
    "categories": [ "Commentary2",
        "Talmud","Rosh"
    ],
    "schema": root.serialize()
    }
    #Index(indx).save()
    if deploy == True:
        url = 'http://' + Helper.server + '/api/v2/raw/index/' + indx["title"].replace(" ", "_")
        indexJSON = json.dumps(indx)
        values = {
            'json': indexJSON,
            'apikey': Helper.apikey
        }
        data = urllib.urlencode(values)
        print url, data
        req = urllib2.Request(url, data)
        try:
            response = urllib2.urlopen(req)
            print response.read()
        except urllib2.HTTPError, e:
            print 'Error code: ', e.code


def parse(text):
    i=0
    kb = re.split(ur"@00הלכות כלאי בגדים(.*?)@00פרק תשיעי", text)
    begadim = kb[1]
    ending = re.split(ur"@00הלכות מקוואות",kb[2])
    bdy = kb[0] + ending[0]
    mikva = ending[1]
    old_numeri = 0
    rosh = []
    kileiggadim =[]
    hilchotmikvaot =[]
    chapters = re.split(ur'(?:@00|@99)([^@]*)', bdy)
    for chapter_num, chapter in zip(chapters[1::2], chapters[2::2]):
        mispar = chapter_num.strip().split(" ")[1]
        if mispar.encode('utf-8') in misparim.keys():
            mispar_numeri = misparim[mispar.encode('utf-8')]
            print mispar_numeri
            if mispar_numeri - old_numeri > 1:
               for i in range(1,mispar_numeri-old_numeri):
                    rosh.append([])
            old_numeri = mispar_numeri
        print mispar
        #if len(chapter)<=1:
         #   pass
        #else:
        perek = []
        a = re.split(ur'@22([^@]*)', chapter)
        for seif, cont in zip(a[1::2], a[2::2]):
            si = []
            content = re.split('@66', cont)
            seif = re.sub(ur'[^א-ת]',"", seif)
            seif = hebrew.heb_string_to_int(seif.strip())
            for num, co in enumerate(content):
                a = re.findall('\[\*\]', co)
                #for b in a:
                    #print b, seif
                si.append(co)
            perek.append(si)
        if len(perek) is not 0:
            rosh.append(perek)
           # print len(rosh)
    search2(rosh)

    #take care of begadim
    b  = re.split(ur'@22([^@]*)',begadim )
    for sei, con in zip(b[1::2], b[2::2]):
        si = []
        conten = re.split('@66', con)
        sei = re.sub(ur'[^א-ת]',"", sei)
        sei = hebrew.heb_string_to_int(sei.strip())
        for num, co in enumerate(conten):
            b = re.findall('\[\*\]', co)
            #for c in b:
                #print c, sei
            si.append(co)
        kileiggadim.append(si)
    b  = re.split(ur'@22([^@]*)', mikva)
    for sei, con in zip(b[1::2], b[2::2]):
        si = []
        conten = re.split('@66', con)
        sei = re.sub(ur'[^א-ת]',"", sei)
        sei = hebrew.heb_string_to_int(sei.strip())
        for num, co in enumerate(conten):
            b = re.findall('\[\*\]', co)
            for c in b:
                print c, sei
            si.append(co)
        hilchotmikvaot.append(si)
    #take care of mikva
    return rosh , kileiggadim,hilchotmikvaot


def search(parsed):
    for i,perek in enumerate(parsed):
        for j,pasuk in enumerate(perek):
            found =  re.finditer(ur'\(דף(.*?)\)', pasuk)
            for find in found:
                daf = find.group(1)
                #text =  find.group(2)
                if daf[len(daf)-1] == '.':
                    #print daf
                    amud = 'a'
                elif daf[len(daf)-1] == ':':
                    amud = 'b'

                new_daf = daf[0:len(daf.strip())].strip()
                #print new_daf
                try:
                    daf_num = hebrew.heb_string_to_int(new_daf)
                    #print str(daf_num) + amud +  " " + str(i) + " " + str(j+1)
                    links.append(link("{}".format(masechet) + "." + str(daf_num) + amud, "Rosh on {}, Hilchot Seder Avodat Yom HaKippurim".format(masechet) + "." + str(i) + "." + str(j+1)))
                    #links.append(link(
                    #match(daf_num, amud, text)
                except KeyError:
                    pass


def search1(parsed, part):
     for i,perek in enumerate(parsed):
           for k, seif in enumerate(perek):
               found =  re.finditer(ur'@44\[דף(.*?)\](.*?)\.', seif)
               for find in found:
                   daf = find.group(1)
                   text =  find.group(2)
                   if daf.strip().split(" ")[1] == u'ע"א':
                       amud = 'a'
                   elif daf.strip().split(" ")[1] == u'ע"ב':
                       amud = 'b'

                   new_daf = daf.strip().split(" ")[0]
                   try:
                       daf_num = hebrew.heb_string_to_int(new_daf)
                       #print str(daf_num) + amud
                       found = matchobj(daf_num, amud, text)
                       line = found[1][0]
                       if line >0:
                        #print "Rosh on {}".format(masechet), daf_num, amud, found[1][0], str(i+1), ",", str(j+1) + ",", str(k+1)
                        talmud = "{}".format(masechet) +  "." + str(daf_num) + amud + "." + str(line)
                        roash = "Rosh on {}".format(masechet) + ", " + part +"." + str(i+1) + "." + str(k+1)

                        links.append(link(talmud,roash))
                   except KeyError:
                       pass


def match(daf_num, amud, text):
    dhlist = []
    makorlist =[]
    index = (daf_num-2)*2
    if amud=="b":
        index= index + 1
    list =text.split(" ")
    string= " ".join(list[0:5])
    string = re.sub('(?:@|[0-9]|<|>|b|\[|\*|\])',"",string)
    dhlist.append(string)
    makorlist.append(shas[index])
    for  line in shas[index]:
        if string in line or line in string:
            print "found", string, line,  daf_num
    #matchobj(dhlist,makorlist)


def matchobj(daf_num, amud, text):
    new_shas =[]
    index = (daf_num-2)*2
    if amud=="b":
        index= index + 1
    list =text.split(" ")
    string= " ".join(list[0:7])
    string = re.sub(ur'(?:@|[0-9]|<|>|b|\[|\*|\])',"",string)
    match_obj = Match(min_ratio=50, guess =True)
    for line in shas[index]:
        new_line = re.sub(ur'<[^<]+?>',"",line)
        new_shas.append(new_line)

    print string, daf_num, amud
    results = match_obj.match_list([string], new_shas)
    return(results)


def clean(parsed):
     rosh=[]
     for i in parsed:
         seif= []
         for j in i:
            j =  re.sub(ur"\(\S?דף.*?\)","", j)
            clean_text = re.sub("(?:@|[0-9]|<|>|b|\[|\*|\]|\/|\(\*\)|[!#])","", j)
            seif.append(clean_text)
            #print clean_text
         if len(seif[0])>1:
            rosh.append(seif)
     return rosh


def clean1(parsed):
    rosh=[]
    for i,perek in enumerate(parsed):

        pr=[]
        for k, seif in enumerate(perek):
            s =[]
            for l in seif:
                #print re.findall(ur"@[0-9[0-9]\S?\[.*?\]\S?@[0-9][0-9]",l )
                #l1 = re.sub(ur"@[0-9[0-9]\S?\[.{1,10}\]\S?@[0-9][0-9]","",l )
                l1 = re.sub(ur"@[0-9[0-9]\S?\[.{1,10}","",l )
                clean_text = re.sub("(?:@|[0-9]|<|>|b|\[|\*|\]|\/|\(\*\)|[!#])","", l1)
                s.append(clean_text)
            pr.append(s)

        rosh.append(pr)
    return rosh


def save_text(text,perek):
    perek = re.sub(" ", "_",perek.strip())
    text_whole = {
    "title": 'Rosh on %s' % masechet,
    "versionTitle": "Vilna Edition",
    "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
    "language": "he",
    "text": text,
    "digitizedBySefaria": True,
    "license": "Public Domain",
    "licenseVetted": True,
    "status": "locked",
    }
    Helper.mkdir_p("../preprocess_json/")
    with open("../preprocess_json/Rosh_on_{}_{}.json".format(masechet,perek), 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api(perek):
    perek1 = re.sub(" ", "_",perek.strip())
    with open("../preprocess_json/Rosh_on_{}_{}.json".format(masechet,perek1), 'r') as filep:
        file_text = filep.read()
    postText("Rosh on %s," % masechet , perek , file_text, False)


def save_default_text(text):
    text_whole = {
    "title": 'Rosh on %s' % masechet,
    "versionTitle": "Vilna Edition",
    "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
    "language": "he",
    "text": text,
    "digitizedBySefaria": True,
    "license": "Public Domain",
    "licenseVetted": True,
    "status": "locked",
    }
    Helper.mkdir_p("../preprocess_json/")
    with open("../preprocess_json/Rosh_on_{}.json".format(masechet), 'w') as out:
            json.dump(text_whole, out)


def run_default_post_to_api():
    with open("../preprocess_json/Rosh_on_{}.json".format(masechet), 'r') as filep:
        file_text = filep.read()
    postdText("Rosh on %s" % masechet ,  file_text, False)

if __name__ == '__main__':
    text = open_file()
#    book_record1()
    body, kilei, mikvaot = parse(text)
    link_tiferet_shmuel(body)
    link_tiferet_shmuel1(kilei,"Hilchot_Kilay_Begadim")
    link_tiferet_shmuel1(mikvaot,"Hilchot_Mikvaot")
    clean_text = clean1(body)
    save_default_text(clean_text)
    run_default_post_to_api()
    search1(kilei,"Hilchot Kilay Begadim")
    search1(mikvaot,"Hilchot Mikvaot")
    cleankilei = clean(kilei)
    cleanmikva = clean(mikvaot)
    save_text(cleankilei,"Hilchot Kilay Begadim")
#    run_post_to_api("Hilchot Kilay Begadim")
#    save_text(cleanmikva,"Hilchot Mikvaot")
#    run_post_to_api("Hilchot Mikvaot")
    #clean kitz ur
  # save_text(kitzur_seder,"Seder HaAvodah BeKitzur")
  # run_post_to_api("Seder HaAvodah BeKitzur")
  # body1 = clean1(body)
  # search(seder_haavoda)
  # search2(body)
#    for lin in links:
#        Helper.postLink(lin)
