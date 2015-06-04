# -*- coding: utf8 -*-
__author__ = 'eliav'
from sefaria.model import *
import re
import json
import urllib2
import urllib
import sys
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
import hebrew


masechet = "Yoma"
masechet_he = ur"יומא"
deploy =False
shas = TextChunk(Ref("%s" % masechet), "he").text


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
        print masechet_he
        return ucd_text


def book_record1():
    b = u"Rosh on %s" % masechet
    a = u" פסקי הראש על " + masechet_he
    root = SchemaNode()
    root.add_title(b, "en", primary=True)
    root.add_title(a, "he", primary=True)
    root.key = b
    seder_avoda = JaggedArrayNode()
    seder_avoda.add_title(u"הלכות סדר עבודת יום הכפורים", "he", primary=True)
    seder_avoda.add_title("Hilchot Seder Avodat Yom haKippurim", "en", primary=True)
    seder_avoda.key = "Hilchot Seder Avodat Yom haKippurim"
    seder_avoda.depth = 1
    seder_avoda.sectionNames = ["siman"]
    seder_avoda.addressTypes = ["Integer"]
    kitzur_seder = JaggedArrayNode()
    kitzur_seder.add_title("Seder haavodah bekitzur", "en", primary=True)
    kitzur_seder.add_title(ur"סדר העבודה בקצור מלשון הרא\"ש זצ\"ל", "he", primary = True)
    kitzur_seder.key = "Seder haavodah bekitzur"
    kitzur_seder.depth = 1
    kitzur_seder.sectionNames = ["Siman"]
    kitzur_seder.addressTypes = ["Integer"]
    perek_shmini = JaggedArrayNode()
    perek_shmini.default = True
    perek_shmini.depth = 2
    perek_shmini.sectionNames = [ "Halacha","Siman"]
    perek_shmini.addressTypes = ["Integer", "Integer"]
    perek_shmini.key = "default"
    root.append(seder_avoda)
    root.append(kitzur_seder)
    root.append(perek_shmini)
    root.validate()
    indx = {
    "title": b,
    "categories": ["Other","Rosh"],
    "schema": root.serialize()
    }
    Index(indx).save()
    if deploy == True:
        url = 'http://www.sefaria.org//api/v2/index/' + indx["title"].replace(" ", "_")
        indexJSON = json.dumps(indx)
        values = {
            'json': indexJSON,
            'apikey': Helper.apikey
        }
        data = urllib2.urlencode(values)
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
            kitzur.append(seif)
            break
        content = re.split('@66', seif)
        siman = []
        for cont in content:
            if len(re.split('(?:@33|@77)', cont)) > 1:
                cont = "<b>" + re.split('(?:@33|@77)', cont)[0] + "</b>" + re.split('(?:@33|@77)', cont)[1]
            else:
                cont = cont[0]
            siman.append(cont)
        hilchot_seder_haavoda.append(siman)
    return hilchot_seder_haavoda, kitzur


def search(parsed):
    for i in parsed:
        for j in i:
            found =  re.finditer(ur'\(דף(.*?)\)(.*?)\(', j)
            for find in found:
                daf = find.group(1)
                text =  find.group(2)
                if daf[len(daf)-1] == '.':
                    #print daf
                    amud = 'a'
                elif daf[len(daf)-1] == ':':
                    amud = 'b'

                new_daf = daf[0:len(daf.strip())].strip()
                #print new_daf
                try:
                    daf_num = hebrew.heb_string_to_int(new_daf)
                    #print str(daf_num) + amud
                    match(daf_num, amud, text)
                except KeyError:
                    pass


def match(daf_num, amud, text):
    index = (daf_num-2)*2
    if amud=="b":
        index= index + 1
    list =text.split(" ")
    string= " ".join(list[0:5])
    string = re.sub('(?:@|[0-9]|<|>|b|\[|\*|\])',"",string)
    print "string is" , string, daf_num
    for  line in shas[index]:
        if string in line or line in string:
            print "found", string, line,  daf_num


def clean(parsed):
     rosh=[]
     for i in parsed:
         seif= []
         for j in i:
            clean_text = re.sub("(?:@|[0-9]|<|>|b|\[|\*|\]|\/|\(\*\))","", j)
            seif.append(clean_text)
            print clean_text
         rosh.append(seif)
     return rosh


def save_text(text):
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
    with open("preprocess_json/Rosh_on_%s.json" % masechet, 'w') as out:
        json.dump(text_whole, out)

def run_post_to_api(perek):
   # Helper.createBookRecord(book_record())
    with open("preprocess_json/Rosh_on_%s.json" % masechet, 'r') as filep:
        file_text = filep.read()
    postText("Rosh on %s," % masechet , perek , file_text, False)


if __name__ == '__main__':
    text = open_file()
#    book_record1()
    seder_haavoda, kitzur_seder = parse_seder_haavoda(text)
    #search()
    clean_text = clean(seder_haavoda)
    save_text(clean_text)
    run_post_to_api("Hilchot Seder Avodat Yom haKippurim")

