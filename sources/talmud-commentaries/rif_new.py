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
shas = TextChunk(Ref("%s" % masechet), "he").text
tzitutim = []


def splitkeepsep(s, sep):
    return reduce(lambda acc, elem: acc[:-1] + [acc[-1] + elem] if elem == sep else acc + [elem], re.split("(%s)" % re.escape(sep), s), [])


def make_link(talmud, rif):
    return {
            "refs": [
               talmud,
                rif ],
            "type": "Commentary",
            "auto": True,
            "generated_by": "Rif_%s" % masechet,
            }


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
        rif = "Rif %s" %masechet + "." + str(i+1) + "." + str(j+1)
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
      a =  ur'רי"ף' + " " + masechet_he
      return {
    "title" : "Rif %s" % masechet ,
    "categories" : [
      # "Commentary2",
        "Talmud",
      "Rif",
        #"Bavli",
        Index().load({"title":masechet}).categories[2],
         #"%s" % masechet
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Rif  %s"% masechet,
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
            "Integer"
        ],
        "key" : "Rif Taanit"
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


def link_to_link(link):
    if len(link.strip().split(" ")) ==2 and link[0]==ur'ד':
        dafamud = link.strip().split(" ")[1]
        amods = dafamud[len(dafamud)-1]
        if amods == ":":
            amod = "b"
        elif amods ==".":
            amod ="a"
        dap = dafamud[0:len(dafamud)-1]

        roman_daf = hebrew.heb_string_to_int(dap.strip())
        return masechet + "." + str(roman_daf) + amod
    elif link[0]==ur'ד':
        pass
        #print link
    elif '.' in link or ":" in link:
        pass
        #print link


def parse(text):
    i=0
    last_daf=0
    rif =[]
    dapim = re.split(ur'@20', text)
    for daf in dapim:
        cut = re.split(ur"(.*?[.:])[^@13(.*?)@77]", daf)
        cut = filter(None, cut)
        dap =[]
        if daf.count('@44')>=1:
            for pars in cut:
                #print pars
                if '@44' in pars:
                    #print pars
                    seif = re.split('@44(.*?)@55(.*?)',pars)
                    seif = filter(None, seif)
                    print len(seif)
                    #if len(seif[0].strip())>10:
                    #dap.append(seif[0])
                    if len(seif)==2:
                        #print seif[1]
                        cont = "<b>" + seif[0] + "</b> " + seif[1]
                        dap.append(cont)
                    else:
                        for bold, not_bold in zip(seif[1::2], seif[2::2]):
                            cont = "<b>" + bold + "</b> " + not_bold
                            #print cont
                            dap.append(cont)

                else:
                    cont = pars
                    if ur'פרק' in cont and len(cont)<15:
                        print len(cont), cont
                    else:
                        dap.append(cont)
                links = re.findall(ur'@13(.*?)@77',cont)
                for link in links:
                    link_to =link_to_link(link)
                    if (len(rif)+1)%2==0:
                        amud = "b"
                        daf = ((len(rif))/2)+1
                    else:
                        amud = "a"
                        daf = ((len(rif))/2)+1
                    if type(link_to) is  str:
                        #print daf, amud, link_to, len(rif)
                        to_link = make_link(link_to, "rif_{}".format(masechet)+"."+ str(daf) + amud + "." + str(len(dap)))
                        if to_link not in tzitutim:
                            #print to_link
                            tzitutim.append(make_link(link_to, "rif_{}".format(masechet)+"."+ str(daf) + amud + "." +str(len(dap))))


        else:
            cont = daf
            cut = re.split(ur"(.*?[.:])[^@13(.*?)@77]",cont)
            cut = filter(None, cut)
            #cut = splitkeepsep(cont, ur"[:.]")
            d = ":"
            #cut =[e+d for e in cont.split(d) if e!="" ]
            for pars in cut:
                links = re.findall(ur'@13(.*?)@77',pars)
                for link in links:
                    link_to = link_to_link(link)
                    if len(links)!=0:
                        if (len(rif)+1)%2==0:
                            amud = "b"
                            daf = ((len(rif)+1)/2)-1
                        else:
                            amud = "a"
                            daf = ((len(rif)+1)/2)
                        if type(link_to) is str:
                            #print daf, amud, link_to
                            to_link = make_link(link_to, "rif_{}".format(masechet)+"."+ str(daf+1) + amud + "." + str(len(dap)+1))
                            if to_link not in tzitutim:
                                #print to_link
                                tzitutim.append(make_link(link_to, "rif_{}".format(masechet)+"."+ str(daf+1) + amud + "." + str(len(dap) + 1)))
                        #link(link_to)
                    #print link_to
                dap.append(pars)
        i+=1
        rif.append(dap)
    #print i
    return rif


def clean(parsed_text):
    clean_pages = []
    for i, page in enumerate (parsed_text):
        clean_chapters = []
        for j, chapter in enumerate(page):
            clean = re.sub(ur'@14(.*?)@77', '(' + r'\1' + ')' , chapter)
            #print type(clean)
            #print clean
            clean_chapter0 = re.sub(ur'@13(.*?)@77', " ", clean)
            clean_chapter1 = re.sub(ur'\(.{1,3}?\)', " ", clean_chapter0)
            clean_chapter2 = re.sub(ur'@[0-9][0-9].\s', " ", clean_chapter1)
            clean_chapter = re.sub(ur'(@[0-9][0-9]|\[.*?\])|[\[\}\*\?]'," ", clean_chapter2)
            #clean_chapter = re.sub(ur'(?:@[0-9][0-9][^\s\u05d3]?|[\*\(\)\[\]\xb0]|[0-9]|#[^\s])',"",clean_chapter2 )
            clean_chapters.append(clean_chapter)
        clean_pages.append(clean_chapters)
    return clean_pages


def save_parsed_text(parsed_text):
    text_whole = {
        "title": 'Rif %s' % masechet,
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
    with open("preprocess_json/Rif_on_%s.json" % masechet, 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    Helper.createBookRecord(book_record())
    with open("preprocess_json/Rif_on_%s.json" % masechet, 'r') as filep:
        file_text = filep.read()
    Helper.postText("Rif %s" % masechet, file_text, False)

if __name__ == '__main__':
    #shas = get_shas()
    #Helper.createBookRecord(book_record())
    text = open_file()
    parsed_text = parse(text)
    links(parsed_text, shas)
    clean_text = clean(parsed_text)
    save_parsed_text(clean_text)
    run_post_to_api()
    #new_tzitutim = list(set(tzitutim))
    Helper.postLink(tzitutim)