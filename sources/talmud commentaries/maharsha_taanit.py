# -*- coding: utf-8 -*-
__author__ = 'eliav'
import re
import json
import urllib2
import sys
from fuzzywuzzy import fuzz
sys.path.insert(1,'../genuzot')
import helperFunctions as Helper
import hebrew
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
log = open('maharsha.log', 'w')
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
    with open("source/maharsha_taanit.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        return ucd_text

#creates a book record
def book_record():
      return {
    "title" : "Chidushei Halachot",
    "categories" : [
        "Other",
        "Maharsha"
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Chidushei Halachot",
                "primary" : True
            },
            {
                "lang" : "he",
                "text" : 'חידושי הלכות',
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
        "key" : "Chidushei Halachot"
    }
	}

#makes a link
def link(maharsha, gemara):
    return {
            "refs": [
               gemara,
                maharsha ],
            "type": "Maharsha in Talmud",
            "auto": True,
            "generated_by": "maharsha_taanit",
            }
            #return link_obj

#gets the number of lines in an amud
def get_lines_number(daf_amud):
    url = 'http://' + Helper.server + '/api/texts/Taanit.' + daf_amud
    response = urllib2.urlopen(url)
    resp = response.read()
    length = len(json.loads(resp)["he"])
    return length

def search_gemara(text, daf_amud, Peirush, diburs = 5):
    num_of_matches = 0
    lines = get_lines_number(daf_amud)
    text = re.sub("'", "", text)
    text = replaceAbbrevs(text)
    dibur = re.split(ur'\s', text)
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
    url = 'http://' + Helper.server + '/api/texts/' + 'Taanit.' + daf_amud + '.' +str(1) + '-' + str(lines)
    response = urllib2.urlopen(url)
    resp = response.read()
    gemara = json.loads(resp)["he"]
    for line in range(0, lines):
        fu = "Gemara, fuzzy matching" + "," + str(fuzz.ratio(maharsha, gemara[line])) + "," + maharsha.encode('utf-8') + "," + gemara[line].encode('utf-8') + "\n"
        partial_fuzz = "Gemara, partial ratio" + "," +  str(fuzz.partial_ratio(maharsha, gemara[line])) + "," + maharsha.encode('utf-8') + "," + gemara[line].encode('utf-8') + "\n"
        fuzzy.write(fu)
        fuzzy.write(partial_fuzz)
        if (diburs > 2 and fuzz.partial_ratio(maharsha, gemara[line]) > 70) or (diburs <=2 and maharsha in gemara[line]):
            rline = line + 1
            num_of_matches += 1
            msg = "found a gemara  match {}  for the maharsha {} in {} , line {} \n".format(gemara[line].encode('utf-8'), maharsha.encode('utf-8'), daf_amud, line)
            print msg
        if line == lines - 1:
            if diburs > 0:
                if num_of_matches == 1:
                    #print link("Chidusheiv Halachot" + "." + daf_amud + ":" + str(Peirush), "Taanit" + "." + daf_amud + ":" + str(rline))
                    links.append(link("Chidushei Halachot" + "." + daf_amud + ":" + str(Peirush), "Taanit" + "." + daf_amud + ":" + str(rline)))
                    #Helper.postLink(link("Maharsha on Taanit" + "." + daf_amud + ":" + str(Peirush), "Taanit" + "." + daf_amud + ":" + str(line)))
                    true_find = "matched!! a maharsha DH {} in the gemara daf {} , line {} \n".format(maharsha.encode('utf-8'), daf_amud, line)
                    print true_find
                   # log.write(true_find)
                    break
                else:
                    diburs -= 1
                    search_gemara(text, daf_amud,Peirush, diburs)
                    break
            if diburs == 0:
                if num_of_matches == 1:
                    links.append(link("Chidushei Halachot" + "." + daf_amud + ":" + str(Peirush), "Taanit" + "." + daf_amud + ":" + str(rline)))
                    #Helper.postLink(link("Maharsha on Taanit" + "." + daf_amud + ":" + str(Peirush), "Taanit" + "." + daf_amud + ":" + str(line)))
                    true_find = "matched!! a maharsha DH {} in the gemara daf {} , line {} \n".format(maharsha.encode('utf-8'), daf_amud, line)
                    print true_find
                    #log.write(true_find)
                    break
                elif num_of_matches > 1:
                    error = "found {} matches for maharsha dibur hamatchil {} in gemara {}\n".format(num_of_matches, maharsha.encode('utf-8'), daf_amud)
                    log.write(error)
                    print error
                else:
                    error = "did not find any matches for maharsha dibur hamatchil {} in gemara {}\n".format(maharsha.encode('utf-8'), daf_amud)
                    log.write(error)
                    print error
#looks for the marsha's reference in rashi
def search_rashi(text, daf_amud, Peirush, diburs = 5):
    num_of_matches = 0
    lines = get_lines_number(daf_amud)
    text = re.sub("'", "", text)
    text = replaceAbbrevs(text)
    dibur = re.split(ur'\s', text)
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
    url = 'http://' + Helper.server + '/api/texts/' + 'Rashi_on_Taanit.' + daf_amud + '.' +str(1) + '-' + str(lines)
    response = urllib2.urlopen(url)
    resp = response.read()
    rashi = json.loads(resp)["he"]
    lines = len(rashi)
    for line in range(0, lines):
        for dh in rashi[line]:
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
                msg = "found a rashi  match {}  for the maharsha {} in {} , line {} \n".format(dibur_hamatchil.encode('utf-8'), maharsha.encode('utf-8'), daf_amud, line)
                print msg
        if line == lines - 1:
            if diburs > 0:
                if num_of_matches == 1:
                    links.append(link("Chidushei Halachot" + "." + daf_amud + ":" + str(Peirush), "Rashi on Taanit" + "." + daf_amud + ":" + str(rline)))
                    #Helper.postLink(link("Maharsha on Taanit" + "." + daf_amud + ":" + str(Peirush), "Rashi on Taanit" + "." + daf_amud + ":" + str(line)))
                    true_find = "matched!! a maharsha DH {} in the rashi daf {}, line {} \n".format(maharsha.encode('utf-8'), daf_amud, line)
                    print true_find
                    #log.write(true_find)
                    break
                else:
                    diburs -= 1
                    search_rashi(text, daf_amud, Peirush, diburs)
                    break
            if diburs == 0:
                if num_of_matches == 1:
                    links.append(link("Chidushei Halachot" + "." + daf_amud + ":" + str(Peirush), "Rashi on Taanit" + "." + daf_amud + ":" + str(rline)))
                    #Helper.postLink(link("Maharsha on Taanit" + "." + daf_amud + ":" + str(Peirush), "Rashi on Taanit" + "." + daf_amud + ":" + str(line)))
                    true_find = "matched!! a maharsha DH {} in the rashi daf {}, line {} \n".format(maharsha.encode('utf-8'), daf_amud, line)
                    print true_find
                    #log.write(true_find)
                    break
                elif num_of_matches > 1:
                    error = "found {} matches for maharsha dibur hamatchil {} in rashi {}\n".format(num_of_matches, maharsha.encode('utf-8'), daf_amud)
                    log.write(error)
                    print error
                else:
                    error = "did not find any matches for maharsha dibur hamatchil {} in rashi {}\n".format( maharsha.encode('utf-8'), daf_amud)
                    log.write(error)
                    print error


#looks for the maharsha's reference in tosafot
def search_tosafot(text, daf_amud, Peirush, diburs = 4):
    text = re.sub("'", "", text)
    text = replaceAbbrevs(text)
    dibur = re.split(ur'\s', text)
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
    lines = get_lines_number(daf_amud)
    url = 'http://' + Helper.server + '/api/texts/' + 'Tosafot_on_Taanit.' + daf_amud + '.' + str(1) + '-' + str(lines)
    response = urllib2.urlopen(url)
    resp = response.read()
    tosafot = json.loads(resp)["he"]
    lines = len(tosafot)
    for line in range(0,lines):
        for dh in tosafot[line]:
            tos = re.split('\.', dh)[0]
            tos = replaceAbbrevs(tos)
            if fuzz.partial_ratio(maharsha, tos) > 70:
                rline = line + 1
                num_of_matches += 1
                msg = "found a Tosafot  match {}  for the maharsha {} in {} , line {} \n".format(tos.encode('utf-8'), maharsha.encode('utf-8'), daf_amud, line)
                print msg
        if line == lines - 1:
            if diburs > 0:
                if num_of_matches == 1:
                    links.append(link("Chidushei Halachot" + "." + daf_amud + ":" + str(Peirush), "Tosafot on Taanit" + "." + daf_amud + ":" + str(rline)))
                    #Helper.postLink(link("Maharsha on Taanit" + "." + daf_amud + ":" + str(Peirush), "Tosafot on Taanit" + "." + daf_amud + ":" + str(line)))
                    true_find = "matched!! a maharsha DH {} in the Tosafot daf {}, line {} \n".format(maharsha.encode('utf-8'), daf_amud, line)
                    print true_find
                    #log.write(true_find)
                    break
                else:
                    diburs -= 1
                    search_tosafot(text, daf_amud, Peirush, diburs)
                    break
            if diburs == 0:
                if num_of_matches == 1:
                    links.append(link("Chidushei Halachot" + "." + daf_amud + ":" + str(Peirush), "Tosafot on Taanit" + "." + daf_amud + ":" + str(rline)))
                    #Helper.postLink(link("Maharsha on Taanit" + "." + daf_amud + ":" + str(Peirush), "Tosafot on Taanit" + "." + daf_amud + ":" + str(line)))
                    true_find = "matched!! a maharsha DH {} in the Tosafot daf {}, line {} \n".format(maharsha.encode('utf-8'), daf_amud, line)
                    print true_find
                    #log.write(true_find)
                    break
                else:
                    error = "did not find any matches for maharsha dibur hamatchil {} in Tosafot {}\n".format( maharsha.encode('utf-8'), daf_amud)
                    log.write(error)
                    print error

# main function, parses the text file lools for reference to rashi or tosafot and calls there functions
def parse_dapim(text):
    shas = 0
    tosafos = 0
    rashi = 0
    amud_num = 'b'
    daf = re.split(ur'@11([^@]*)', text)
    chidushei_halachot = [[],[]]

    for daf_num, content in zip(daf[1::2], daf[2::2]):
        cut_books = re.split(ur'@66([^@]*)', content)
        amudim = re.split(ur'@44ע"ב', cut_books[0])
        for amud in amudim:
            DH = []
            if amud_num == 'b':
                amud_num = 'a'
            else:
                amud_num = 'b'
            halachot = re.split(ur'@44',amud)
            for i, verse in enumerate(halachot):
                pverse = re.sub(ur'@..', "", verse)
                DH.append(pverse)
                number = hebrew.heb_string_to_int(daf_num[3:])
                if ur'רש"י' in verse[0:10]:
                    search_rashi(verse, str(number) + amud_num, i+1)
                    rashi += 1
                    pass
                elif ur'תוס' in verse[0:10]:
                    search_tosafot(verse, str(number) + amud_num, i+1)
                    tosafos += 1
                    pass
                else:
                    search_gemara(verse, str(number) + amud_num, i+1)
                    shas += 1
                    pass
            chidushei_halachot.append(DH)
    #print links[0]
    print "shas", shas, "rashi", rashi, "tosafot", tosafos
    return chidushei_halachot

def save_parsed_text(text):
    text_whole = {
        "title": 'Maharsha on Taanit',
        "versionTitle": "Presburg : A. Schmid, 1842",
        "versionSource": "http://www.worldcat.org/title/perush-radak-al-ha-torah-sefer-bereshit/oclc/867743220",
        "language": "he",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Maharsha_on_Taanit.json", 'w') as out:
        json.dump(text_whole, out)

def run_post_to_api():
    Helper.createBookRecord(book_record())
    with open("preprocess_json/Maharsha_on_Taanit.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Chidushei Halachot", file_text, False)

if __name__ == '__main__':
    text = open_file()
    parsed_text = parse_dapim(text)
    Helper.createBookRecord(book_record())
    save_parsed_text(parsed_text)
    run_post_to_api()
    Helper.postLink(links)


