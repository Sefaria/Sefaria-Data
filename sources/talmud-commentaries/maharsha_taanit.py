# -*- coding: utf-8 -*-
__author__ = 'eliav'
import re
import json
import urllib2
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
tosafot = TextChunk(Ref("Tosafot on %s" % masechet), "he").text
rashi = TextChunk(Ref("Rashi on %s" % masechet), "he").text

Abbreviations = {
'אא"כ':'אלא אם כן',
'א"כ':'אם כן',
'אע"ג':'אף על גב',
'אע"פ':'אף על פי',
'א"ר':'אמר רב',
'ב"ה':'בית הלל',
'ב"ש':'בית שמאי',
"ג'":"שלש",
"ד'":"ארבע",
'ה"מ':'הני מילי',
'ה"נ':'הכי נמי',
'הנ"מ':'הני מילי',
'ה"ק':'הכי קאמר',
"י'":'עשר',
'י"א':'יש אומרים',
'יו"ט':'יום טוב',
'למ"ד':'למאן דאמר',
'מ"מ':'מכל מקום',
'מנה"מ':'מנא הני מילי',
'קמ"ל':'קא משמע לן',
'קס"ד':'קא סלקא דעתך',
'ק"ש':'קרית שמע',
"ר'": "רב" ,
'ר"מ': 'רבי מאיר' ,
'ר"ע' : 'רבי עקיבא',
'ת"ש':'תא שמע',
'ת"ר':'תנו רבנן'
}
links = []
log = open('logs/{}/maharsha_chidushei_halachot_{}.log'.format(masechet,masechet), 'w')
abbs = open('abbs.txt', 'wb')
fuzzy = open('fuzzywuzzy.txt','wb')


def replaceAbbrevs(text):
        unabbrevText = text
        words = text.split(" ")
        for word in words:
            if '"' not in word:
                unabbrev = word
            else:
                if word.encode('utf-8') in Abbreviations:
                    unabbrev = Abbreviations[word.encode('utf-8')]
                    unabbrev= unabbrev.decode('utf-8')
                else:
                    abbs.write(word.encode('utf-8') + "\n")
                    unabbrev = word
            unabbrevText = unabbrevText.replace(word, unabbrev)

        return unabbrevText


#opens the maharsha text file and stores it
def open_file():
    with open("source/maharsha_%s.txt" % masechet, 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        return ucd_text


#creates a book record
def book_record():
    a= " חידושי הלכות על מסכת " + masechet_he.encode('utf-8')
    return {
    "title" : "Chidushei Halachot on %s" % masechet,
    "categories" : [
        "Commentary2",
        "Talmud",
        "Bavli",
        Index().load({"title":masechet}).categories[2],
         "%s" % masechet
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Chidushei Halachot on %s" % masechet,
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
        "key" : "Chidushei Halachot on %s" %masechet
    }
	}


#makes a link
def link(maharsha, gemara):
    return {
            "refs": [
               gemara,
                maharsha ],
            "type": "Commentary",
            "auto": True,
            "generated_by": "maharsha_%s" % masechet,
            }
            #return link_obj


def search_gemara(text, daf,amud, Peirush, diburs = 5):
    num_of_matches = 0
    text = re.sub("'", "", text)
    text = replaceAbbrevs(text)
    dibur = re.split(ur'\s', text)
    if len(dibur) <5:
        return
    if diburs == 5:
        maharsha = dibur[2] + " " + dibur[3] + " " + dibur[4] + " " + dibur[5]
    elif diburs == 4:
        maharsha = dibur[3] + " " + dibur[4] + " " + dibur[5]
    elif diburs == 3:
        maharsha = dibur[3] + " " + dibur[4]
    elif diburs == 2:
        maharsha = dibur[3]
    elif diburs == 1:
        maharsha = dibur[4]
    elif diburs == 0:
        maharsha = dibur[2]
    print "daf is",daf
    if amud == "a":
        index = (daf * 2) - 2
    if amud == "b":
        index = (daf * 2) - 1
    print "index is", index
    lines = len(shas[index])
    for linen, line in enumerate(shas[index]):
        fu = "Gemara, fuzzy matching" + "," + str(fuzz.ratio(maharsha, line)) + "," + maharsha.encode('utf-8') + "," + line.encode('utf-8') + "\n"
        partial_fuzz = "Gemara, partial ratio" + "," +  str(fuzz.partial_ratio(maharsha, line)) + "," + maharsha.encode('utf-8') + "," + line.encode('utf-8') + "\n"
        fuzzy.write(fu)
        fuzzy.write(partial_fuzz)
        if (diburs > 2 and fuzz.partial_ratio(maharsha, line) > 70) or (diburs <=2 and maharsha in line):
            rline = linen + 1
            num_of_matches += 1
            msg = "found a gemara  match {}  for the maharsha {} in {} , line {} \n".format(line.encode('utf-8'), maharsha.encode('utf-8'), str(daf).encode('utf-8') + amud, linen)
            print msg
        if linen == lines - 1:
            if diburs > 0:
                if num_of_matches == 1:
                    #print link("Chidusheiv Halachot" + "." + daf_amud + ":" + str(Peirush), "%s" 5 masechet + "." + daf_amud + ":" + str(rline))
                    links.append(link("Chidushei Halachot on %s" % masechet + "." + str(daf) + amud + ":" + str(Peirush), "%s" % masechet + "." + str(daf) + amud + ":" + str(rline)))
                    #Helper.postLink(link("Maharsha on %s" % masechet + "." + daf_amud + ":" + str(Peirush), "%s" % masechet + "." + daf_amud + ":" + str(line)))
                    true_find = "matched!! a maharsha DH {} in the gemara daf {} , line {} \n".format(maharsha.encode('utf-8'), str(daf) + amud, linen)
                    print true_find
                   # log.write(true_find)
                    break
                else:
                    diburs -= 1
                    search_gemara(text, daf, amud,Peirush, diburs)
                    break
            if diburs == 0:
                if num_of_matches == 1:
                    links.append(link("Chidushei Halachot on %s" % masechet + "." + str(daf) + amud + "." + str(Peirush), "%s" % masechet + "." + str(daf) + amud + "." + str(rline)))
                    #Helper.postLink(link("Maharsha on %s" 5 masechet  + "." + daf_amud + ":" + str(Peirush), "%s" % masechet + "." + daf_amud + ":" + str(line)))
                    true_find = "matched!! a maharsha DH {} in the gemara daf {} , line {} \n".format(maharsha.encode('utf-8'), str(daf) +amud, linen)
                    print true_find
                    #log.write(true_find)
                    break
                elif num_of_matches > 1:
                    error = "found {} matches for maharsha dibur hamatchil {} in gemara {}\n".format(num_of_matches, maharsha.encode('utf-8'), str(daf) + amud)
                    log.write(error)
                    print error
                else:
                    error = "did not find any matches for maharsha dibur hamatchil {} in gemara {}\n".format(maharsha.encode('utf-8'), str(daf) + amud)
                    log.write(error)
                    print error


#looks for the marsha's reference in rashi
def search_rashi(text, daf, amud, Peirush, diburs = 5):
    num_of_matches = 0
    if amud == "a":
        index = (daf * 2) - 2
    if amud == "b":
        index = (daf * 2) - 1
    lines = len(rashi[index])
    text = re.sub("'", "", text)
    text = replaceAbbrevs(text)
    dibur = re.split(ur'\s', text)
    if len(dibur) <5:
        diburs= len(dibur)
    if diburs == 5:
        maharsha = dibur[2] + " " + dibur[3] + " " + dibur[4] + " " + dibur[5]
    elif diburs == 4:
        maharsha = dibur[3] + " " + dibur[4] + " " + dibur[5]
    elif diburs == 3:
        maharsha = dibur[3] + " " + dibur[4]
    elif diburs == 2:
        maharsha = dibur[3]
    elif diburs == 1:
        maharsha = dibur[4]
    elif diburs ==0:
        maharsha = dibur[2]
    for line in range(0, lines):
        for dh in rashi[index][line]:
            dibur_hamatchil = re.split('-', dh)[0]
            dibur_hamatchil = replaceAbbrevs(dibur_hamatchil)
            fu = "Rashi, fuzzy matching" + "," + str(fuzz.ratio(maharsha, dibur_hamatchil)) + "," + maharsha.encode('utf-8') + "," + dibur_hamatchil.encode('utf-8') + "\n"
            partial_fuzz = "Rashi, partial ratio" + "," +  str(fuzz.partial_ratio(maharsha, dibur_hamatchil)) + "," + maharsha.encode('utf-8') + "," + dibur_hamatchil.encode('utf-8') + "\n"
            fuzzy.write(fu)
            fuzzy.write(partial_fuzz)
            #if maharsha in dibur_hamatchil:
            if (diburs > 2 and fuzz.partial_ratio(maharsha, dibur_hamatchil) > 70) or (diburs <= 2 and maharsha in dibur_hamatchil):
                rline = line + 1
                num_of_matches += 1
                msg = "found a rashi  match {}  for the maharsha {} in {} , line {} \n".format(dibur_hamatchil.encode('utf-8'), maharsha.encode('utf-8'), daf,amud, line)
                print msg
        if line == lines - 1:
            if diburs > 0:
                if num_of_matches == 1:
                    #links.append(link("Chidushei Halachot on %s" %masechet + "." + daf_amud + ":" + str(Peirush), "Rashi on %s" % masechet + "." + daf_amud + ":" + str(rline)))
                    print "rashi peirush", Peirush
                    print "Chidushei Halachot on %s" % masechet + "." + str(daf)+amud + ":" + str(Peirush), "%s" % masechet  + "." + str(daf) +amud + ":" + str(rline)
                    links.append(link("Chidushei Halachot on %s" % masechet + "." + str(daf) +amud + ":" + str(Peirush), "Rashi on %s" % masechet + "." + str(daf) + amud + ":" + str(rline)))
                    #Helper.postLink(link("Maharsha on %s" % masechet + "." + daf_amud + ":" + str(Peirush), "Rashi on %s" % masechet + "." + daf_amud + ":" + str(line)))
                    true_find = "matched!! a maharsha DH {} in the rashi daf {}, line {} \n".format(maharsha.encode('utf-8'), str(daf)+amud, line)
                    print true_find
                    #log.write(true_find)
                    break
                else:
                    diburs -= 1
                    search_rashi(text, daf,amud, Peirush, diburs)
                    break
            if diburs == 0:
                if num_of_matches == 1:
                    #links.append(link("Chidushei Halachot on %s" % masechet + "." + daf_amud + ":" + str(Peirush), "Rashi on %s" % masechet + "." + daf_amud + ":" + str(rline)))
                    links.append(link("Chidushei Halachot on %s" % masechet + "." + str(daf)+amud + "." + str(Peirush), "%s" % masechet  + "." + str(daf) +amud + "." + str(rline)))
                    print "Chidushei Halachot on %s" % masechet + "." + str(daf)+amud + "." + str(Peirush), "%s" % masechet  + "." + str(daf) +amud + "." + str(rline)
                    #Helper.postLink(link("Maharsha on %s" % masechet + "." + daf_amud + ":" + str(Peirush), "Rashi on %s" % masechet + "." + daf_amud + ":" + str(line)))
                    true_find = "matched!! a maharsha DH {} in the rashi daf {}, line {} \n".format(maharsha.encode('utf-8'), str(daf) + amud, line)
                    print true_find
                    #log.write(true_find)
                    break
                elif num_of_matches > 1:
                    error = "found {} matches for maharsha dibur hamatchil {} in rashi {}\n".format(num_of_matches, maharsha.encode('utf-8'), str(daf)+amud)
                    log.write(error)
                    print error
                else:
                    error = "did not find any matches for maharsha dibur hamatchil {} in rashi {}\n".format( maharsha.encode('utf-8'), str(daf) +amud)
                    log.write(error)
                    print error


#looks for the maharsha's reference in tosafot
def search_tosafot(text, daf, amud, Peirush, diburs = 4):
    text = re.sub("'", "", text)
    text = replaceAbbrevs(text)
    dibur = re.split(ur'\s', text)
    print "length of dibur is:" ,len(dibur)
    if len(dibur)< 5:
        return
    if diburs == 4:
        maharsha = dibur[2] + " " + dibur[3] + dibur[4] + dibur[5]
    elif diburs == 3:
         maharsha = dibur[3] + " " + dibur[4] + " " + dibur[5]
    elif diburs == 2:
        maharsha = dibur[3] + " " + dibur[4]
    elif diburs == 1:
        maharsha = dibur[3]
    elif diburs == 0:
        maharsha = dibur[4]
    num_of_matches = 0
    if amud == "a":
        index = (daf * 2) - 2
    if amud == "b":
        index = (daf * 2) - 1
    lines = len(tosafot[index])
    for line in range(0,lines):
        print tosafot[index]
        for dh in tosafot[index][line]:
            tos = re.split('\.', dh)[0]
            tos = replaceAbbrevs(tos)
            fu = "Tosafot, fuzzy matching" + "," + str(fuzz.ratio(maharsha, tos)) + "," + maharsha.encode('utf-8') + "," + tos.encode('utf-8') + "\n"
            partial_fuzz = "Rashi, partial ratio" + "," +  str(fuzz.partial_ratio(maharsha, tos)) + "," + maharsha.encode('utf-8') + "," + tos.encode('utf-8') + "\n"
            fuzzy.write(fu)
            fuzzy.write(partial_fuzz)
            if fuzz.partial_ratio(maharsha, tos) > 70:
                rline = line + 1
                num_of_matches += 1
                msg = "found a Tosafot  match {}  for the maharsha {} in {} , line {} \n".format(tos.encode('utf-8'), maharsha.encode('utf-8'), str(daf),amud, line)
                print msg
        if line == lines - 1:
            if diburs > 0:
                if num_of_matches == 1:
                    #links.append(link("Chidushei Halachot on %s" % masechet + "." + daf_amud + ":" + str(Peirush), "Tosafot on %s" % masechet + "." + daf_amud + ":" + str(rline)))
                    links.append(link("Chidushei Halachot on %s" % masechet + "." + str(daf) + amud + "." + str(Peirush), "Tosafot on %s" % masechet + "." + str(daf)+amud + "." + str(rline)))
                    #Helper.postLink(link("Maharsha on %s" % masechet + "." + daf_amud + ":" + str(Peirush), "Tosafot on %s" % masechet + "." + daf_amud + ":" + str(line)))
                    true_find = "matched!! a maharsha DH {} in the Tosafot daf {}, line {} \n".format(maharsha.encode('utf-8'), str(daf)+amud, line)
                    print true_find
                    #log.write(true_find)
                    break
                else:
                    diburs -= 1
                    search_tosafot(text, daf,amud, Peirush, diburs)
                    break
            if diburs == 0:
                if num_of_matches == 1:
                    #links.append(link("Chidushei Halachot on %s" % masechet + "." + daf_amud + ":" + str(Peirush), "Tosafot on %s" % masechet + "." + daf_amud + ":" + str(rline)))
                    links.append(link("Chidushei Halachot on %s" % masechet + "." + str(daf)+amud + ":" + str(Peirush), "%s" % masechet + "." + str(daf)+amud + ":" + str(rline)))
                    #Helper.postLink(link("Maharsha on %s" % masechet + "." + daf_amud + ":" + str(Peirush), "Tosafot on %s" % masechet + "." + daf_amud + ":" + str(line)))
                    true_find = "matched!! a maharsha DH {} in the Tosafot daf {}, line {} \n".format(maharsha.encode('utf-8'), str(daf)+amud, line)
                    print true_find
                    #log.write(true_find)
                    break
                else:
                    error = "did not find any matches for maharsha dibur hamatchil {} in Tosafot {}\n".format( maharsha.encode('utf-8'), str(daf) +amud)
                    log.write(error)
                    print error


# main function, parses the text file lools for reference to rashi or tosafot and calls there functions
def parse_dapim(text):
    old_num = 1
    shas = 0
    count = 1
    ncount = 1
    tosafos = 0
    rashi = 0
    no_b=False
    amud_num = 'b'
    daf = re.split(ur'@[0-9][0-9](דף[^@]*)', text)
    print "length daf", len(daf)
    #print len(daf)
    chidushei_halachot = [[],[]]
    for daf_num, content in zip(daf[1::2], daf[2::2]):
        #print daf_num
        count+=1
        cut_books = re.split(ur'@66([^@]*)', content)
        if len(re.findall(ur'[0-9][0-9]ע"ב',cut_books[0] ))==0:
            #print "is zero", daf_num
            no_b= True
        amudim = re.split(ur'(?:@44|@11)ע"ב', cut_books[0])
        for amud in amudim:
            if len(amudim)<2:
                print len(amudim), daf_num
            DH = []
            if amud_num == 'b':
                amud_num = 'a'
            elif no_b == True:
                amud_num = 'a'
            else:
                amud_num='b'
            halachot = re.split(ur'@44',amud)
            for i, verse in enumerate(halachot):
                pverse = re.sub(ur'@..', "", verse)
                if len(pverse)<3:
                    pverse= " "
                DH.append(pverse)
                if len(daf_num[3:])>3:
                    print "longer than 3", daf_num[3:], number
                number = hebrew.heb_string_to_int(re.sub("'","",daf_num[3:].strip()))
                if (number - old_num) <0 or (number - old_num) >1:
                    print "diff", number - old_num, daf_num
                old_num = number
                #print number
                if ur'רש"י' in verse[0:10]:
                    search_rashi(verse, number , amud_num, i+1)
                    rashi += 1
                    pass
                elif ur'תוס' in verse[0:10]:
                   # search_tosafot(verse, number , amud_num, i+1)
                    tosafos += 1
                    pass
                else:
                   search_gemara(verse, number , amud_num, i+1)
                   shas += 1
                   pass
            ncount+=1
            if no_b == True:
                chidushei_halachot.append(DH)
                chidushei_halachot.append([])
                no_b= False
                break
            chidushei_halachot.append(DH)

    #print links[0]
    print "shas", shas, "rashi", rashi, "tosafot", tosafos
    print "count", count, "ncount", ncount
    return chidushei_halachot


def save_parsed_text(text):
    text_whole = {
        "title": 'Maharsha on %s' %masechet,
        "versionTitle": "Vilna Edition",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "language": "he",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Maharsha_on_%s.json" % masechet, 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
   # Helper.createBookRecord(book_record())
    with open("preprocess_json/Maharsha_on_%s.json" % masechet, 'r') as filep:
        file_text = filep.read()
    Helper.postText("Chidushei Halachot on %s" % masechet, file_text, False)

if __name__ == '__main__':
    text = open_file()
    parsed_text = parse_dapim(text)
    print len(parsed_text)
    Helper.createBookRecord(book_record())
    save_parsed_text(parsed_text)
    run_post_to_api()
    Helper.postLink(links)
