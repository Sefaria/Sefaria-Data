# -*- coding: utf-8 -*-
__author__ = 'eliav'
import urllib2
from fuzzywuzzy import fuzz
import sys
import json
import re
from sefaria.model import *
sys.path.insert(1, '../genuzot')
import helperFunctions as Helper
import hebrew

masechet = str(sys.argv[1])
masechet_he = Index().load({"title":masechet}).get_title("he")
log = open('log_%s_rif.txt' % masechet, 'w')
tzitutim = []


def link(talmud, rif):
    return {
            "refs": [
               talmud,
                rif ],
            "type": "Rif in Talmud",
            "auto": True,
            "generated_by": "Rif_%s" % masechet,
            }


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


def matching(quote, daf, amud,i,j,shas, words, ratio):
    search_quote = " ".join(quote[0:words])
    search_quote = re.sub('(?:@[0-9]|[0-9])', "", search_quote)
    daf_amud = str(daf) + amud
    index = ((daf-2)*2)+1
    if amud == 'a':
        index = index - 1
    found = 0
    str_line = 0
    for line_num, line in enumerate(shas[index]):
        if fuzz.partial_ratio(search_quote, line) > ratio:
            str_line = line_num
            found += 1
    if found > 1:
        if ratio <= 98:
            ratio += 1
            matching(quote,daf,amud,i,j,shas,words, ratio)
        else:
            shefa = "found too many: "+str(found)+ daf_amud+ "fuzz partial ratio is: "+str(fuzz.partial_ratio(line,search_quote))
            log.write(shefa)
            print shefa
            pass
    if found == 1:
        sucses = "found!" + daf_amud
        log.write(sucses)
        talmud = masechet + "." + daf_amud+"." + str(str_line+1)
        rif = "Rif on %s" %masechet + "." + str(i+1) + "." + str(j+1)
        tzitutim.append(link(talmud, rif))
        return
    if found == 0:
        if words == 0:
            nada = "did not find" + daf_amud + "ratio is: " + str(ratio)
            log.write(nada)
            print nada
            return
        matching(quote,daf,amud,i,j,shas,words-1, ratio)


def book_record():
      a = u" הר\"יף על " + masechet_he
      return {
    "title" : "Rif on %s" % masechet ,
    "categories" : [
        "Other",
        "Rif"
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Rif on %s"% masechet,
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
           "Integer",
            "Integer"
        ],
        "key" : "Rif on Taanit"
    }
	}


def open_file():
    with open("source/rif_on_%s.txt" % masechet, 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        return ucd_text


def links(clean_text, shas):
    for i, page in enumerate (clean_text):
        for j,chapter in enumerate(page):
            a = re.finditer(ur"@88(.+?)@77(.+)", chapter)
            for link in a:
                heb_links= re.split(" ",link.group(1))
                daf =heb_links[1]
                amud = heb_links[2]
                if amud[2]==ur'א':
                      eng_amud = 'a'
                elif amud[2]==ur'ב':
                    eng_amud=ur'b'
                daf = hebrew.heb_string_to_int(daf)
                quote = re.split(" ",link.group(2).strip())
                matching(quote, daf, eng_amud,i,j, shas,words =len(quote), ratio = 70)


def parse(text):
    rif =[]
    dapim = re.split(ur'@66',text )
    for daf in dapim:
        diburs = re.split(ur'@44',daf)
        diburim = []
        for dibur in diburs:
            cut = re.split(ur'@55',dibur)
            if len(cut) > 1:
                matchil = "<b>" + cut[0] +"</b>" + cut[1]
            else:
                if len(cut)==0 or len(cut[0])==0:
                    pass
                else:
                    matchil=  cut[0]
            if len(matchil) <= 1:
                pass
            else:
                diburim.append(matchil)
        rif.append(diburim)
    return rif


def clean(parsed_text):
    clean_pages = []
    for i, page in enumerate (parsed_text):
        clean_chapters = []
        for j, chapter in enumerate(page):
            clean_chapter = re.sub(ur'(?:@[0-9][0-9][^\s\u05d3]?|[\*\(\)\[\]\xb0]|[0-9]|#[^\s])',"",chapter )
            clean_chapters.append(clean_chapter)
        clean_pages.append(clean_chapters)
    return clean_pages


def save_parsed_text(parsed_text):
    text_whole = {
        "title": 'Rif on %s' % masechet,
        "versionTitle": "Vilna",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "language": "he",
        "text": parsed_text,
        "digitizedBySefaria": True,
        "license": "Public Domain",
        "licenseVetted": True,
        "status": "locked",
    }
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Rif_on_%s.json" % masechet, 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    Helper.createBookRecord(book_record())
    with open("preprocess_json/Rif_on_%s.json" % masechet, 'r') as filep:
        file_text = filep.read()
    Helper.postText("Rif on %s" % masechet, file_text, False)

if __name__ == '__main__':
    shas = get_shas()
    #Helper.createBookRecord(book_record())
    text = open_file()
    parsed_text = parse(text)
    #links(parsed_text, shas)
    clean_text = clean(parsed_text)
    save_parsed_text(clean_text)
    run_post_to_api()
    #Helper.postLink(tzitutim)