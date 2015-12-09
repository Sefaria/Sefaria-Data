# -*- coding: utf8 -*-
__author__ = 'eliav'
from sefaria.model import *
import re
import json
import urllib2
import urllib
import sys
from HTMLParser import HTMLParser
from fuzzywuzzy import fuzz
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
import hebrew
sys.path.insert(0, '../Match/')
from match import Match

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

links = []
masechet = "Yoma"
masechet_he = ur"יומא"
deploy =True
shas = TextChunk(Ref("%s" % masechet), "he").text
log =open("../../Match Logs/Talmud/{}/log_rosh_on_{}.txt".format(masechet,masechet),"w")


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
                       #print "Rosh on {}".format(masechet), daf_num, amud, found[1][0], str(i+1), ",", str(j+1) + ",", str(k+1)
                       talmud = "{}".format(masechet) +  "." + str(daf_num) + amud
                       roash = "Rosh on {}".format(masechet) +"." + str(i+1) + "." + str(j+1) + "." + str(k+1)
                       links.append(link(talmud,roash))
                   except KeyError:
                       pass


def link(talmud, roash):
    return {
            "refs": [
               talmud,
                roash ],
            "type": "Rosh in Talmud",
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
    with open("source/Rosh_on_%s.txt" % masechet, 'r') as filep:
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
    seder_avoda = JaggedArrayNode()
    seder_avoda.add_title(u"הלכות סדר עבודת יום הכפורים", "he", primary=True)
    seder_avoda.add_title("Hilchot Seder Avodat Yom HaKippurim", "en", primary=True)
    seder_avoda.key = "Hilchot Seder Avodat Yom HaKippurim"
    seder_avoda.depth = 2
    seder_avoda.sectionNames = ["Seif", "siman"]
    seder_avoda.addressTypes = ["Integer","Integer"]
    kitzur_seder = JaggedArrayNode()
    kitzur_seder.add_title("Seder HaAvodah BeKitzur", "en", primary=True)
    kitzur_seder.add_title(ur'סדר העבודה בקצור מלשון הרא"ש זצ"ל', "he", primary = True)
    kitzur_seder.key = "Seder HaAvodah BeKitzur"
    kitzur_seder.depth = 1
    kitzur_seder.sectionNames = ["Siman"]
    kitzur_seder.addressTypes = ["Integer"]
    perek_shmini = JaggedArrayNode()
    perek_shmini.default = True
    perek_shmini.depth = 3
    perek_shmini.sectionNames = ["Perek", "Halacha", "siman"]
    perek_shmini.addressTypes = ["Integer", "Integer", "Integer"]
    perek_shmini.key = "default"
    root.append(seder_avoda)
    root.append(kitzur_seder)
    root.append(perek_shmini)
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
        url = 'http://' + Helper.server + '/api/v2/index/' + indx["title"].replace(" ", "_")
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


def parse_seder_haavoda(text):
    i=0
    hilchot_seder_haavoda = []
    kitzur = []
    cut = re.split("@00",text)
    seder_haavoda = cut[0]
    seifim = re.split('@22', seder_haavoda)
    for seif in seifim:
        if ur'סדר עבודה בקצור' in seif:
            i = 1
            continue
        if i > 0:
            if "@11" in seif:
                new_seif =re.split(ur"@33",seif)

                kitz =  "<b>" +  re.sub(ur"@11","",new_seif[0]) + '</b>' + new_seif[1]
            kitzur.append(kitz)
            break
        content = re.split('@66', seif)
        siman = []
        for cont in content:
           # print re.findall(ur"(\(דף [\u05d0-\u05ea][\u05d0-\u05ea][\.:]\))", cont)
            if len(re.split('(?:@33|@77)', cont)) > 1:
                cont = "<b>" + re.split('(?:@33|@77)', cont)[0] + "</b>" + re.split('(?:@33|@77)', cont)[1]
            else:
                cont = cont[0]
            siman.append(cont)
        hilchot_seder_haavoda.append(siman)
    default = cut[1]
    body = []
    chapters = re.split(ur'(?:@00|@99)([^@]*)', default)
    perek= chapters[1]
    heb_num= perek.strip().split(" ")[1]
    numbers = {u"ראשון":1,u"שני":2,u"שלישי":3,u"רביעי":4,u"חמישי":5,u"שישי":6,u"שביעי":7,u"שמיני":8}
    chapter =  numbers[heb_num]
    while chapter - len(body) > 1:
        body.append([])
    a = re.split(ur'@22([^@]*)', chapters[2])
    prk=[]
    for seif, cont in zip(a[1::2], a[2::2]):
        #print seif
        content = re.split('@66', cont)
        sif =[]
        for siman in content:
            #print siman
            sif.append(siman)
        prk.append(sif)
    body.append(prk)
    #print len(body)
    return hilchot_seder_haavoda, kitzur, body


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


def search1(parsed):
    for i in parsed:
       for k in i:
           for j in k:
               found =  re.finditer(ur'@44\[דף(.*?)\](.*?)\(', j)
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
                       match(daf_num, amud, text)
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
    match_obj = Match(min_ratio=55, guess =True)
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
            clean_text = re.sub("(?:@|[0-9]|<|>|b|\[|\*|\]|\/|\(\*\))","", j)
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
                clean_text = re.sub("(?:@|[0-9]|<|>|b|\[|\*|\]|\/|\(\*\)|#)","", l1)
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
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Rosh_on_{}_{}.json".format(masechet,perek), 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api(perek):
    perek1 = re.sub(" ", "_",perek.strip())
    with open("preprocess_json/Rosh_on_{}_{}.json".format(masechet,perek1), 'r') as filep:
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
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Rosh_on_{}.json".format(masechet), 'w') as out:
            json.dump(text_whole, out)


def run_default_post_to_api():
    with open("preprocess_json/Rosh_on_{}.json".format(masechet), 'r') as filep:
        file_text = filep.read()
    postdText("Rosh on %s" % masechet ,  file_text, False)

if __name__ == '__main__':
    text = open_file()
    book_record1()
    seder_haavoda, kitzur_seder, body = parse_seder_haavoda(text)
    #print len(body)
    #print body[7][0][0]
    # parse perek shmini
    search(seder_haavoda)
    search2(body)
    clean_text = clean(seder_haavoda)
    save_text(clean_text,"Hilchot Seder Avodat Yom HaKippurim")
    run_post_to_api("Hilchot Seder Avodat Yom HaKippurim")
    #clean kitz ur
    save_text(kitzur_seder,"Seder HaAvodah BeKitzur")
    run_post_to_api("Seder HaAvodah BeKitzur")
    body1 = clean1(body)
    save_default_text(body1)
    run_default_post_to_api()
    for lin in links:
        Helper.postLink(lin)
