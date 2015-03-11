# -*- coding: utf-8 -*-
__author__ = 'eliav'
import re
import json
import urllib2
import sys
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
log = open('maharsha.log', 'w')
abbs = open('abbs.txt', 'wb')
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
    "title" : "Maharsha on Taanit",
    "categories" : [
        "Other",
        "Maharsha"
    ],
    "schema" : {
        "titles" : [
            {
                "lang" : "en",
                "text" : "Maharsha on Taanit",
                "primary" : True
            },
            {
                "lang" : "he",
                "text" : 'מהרש"א על תענית',
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
        "key" : "Maharsha on Taanit"
    }
	}

#makes a link
def link(maharsha, gemara):
     link_obj = {
                                "refs": [
                                   gemara(),
                                    maharsha ],
                                "type": "Mishnah in Talmud",
                                "auto": True,
                                "generated_by": "connect_mishnah",
                                }

#gets the number of lines in an amud
def get_lines_number(daf_amud):
    url = 'http://' + Helper.server + '/api/texts/Taanit.' + daf_amud
    response = urllib2.urlopen(url)
    resp = response.read()
    length = len(json.loads(resp)["he"])
    return length

def search_gemara(text, daf_amud, diburs = 2):
    #n = 0
    num_of_matches = 0
    lines = get_lines_number(daf_amud)
    text = re.sub("'", "", text)
    text = replaceAbbrevs(text)
    dibur = re.split(ur'\s', text)
    if diburs == 2:
        maharsha = dibur[3] + " " + dibur[4]
    elif diburs == 1:
        maharsha = dibur[3]
    elif diburs == 3:
        maharsha = dibur[3] + " " + dibur[4] + " " + dibur[5]
    elif diburs == 0:
        maharsha = dibur[4]
    url = 'http://' + Helper.server + '/api/texts/' + 'Taanit.' + daf_amud + '.' +str(1) + '-' + str(lines)
    response = urllib2.urlopen(url)
    resp = response.read()
    gemara = json.loads(resp)["he"]
    for line in range(0, lines):
        if maharsha in gemara[line]:
            num_of_matches += 1
            msg = "found a gemara  match {}  for the maharsha {} in {} , line {} \n".format(gemara[line].encode('utf-8'), maharsha.encode('utf-8'), daf_amud, line)
            #log.write(msg)
            #print msg
        if line == lines - 1:
            if num_of_matches > 1:
                if diburs == 3 or diburs ==0:
                    error = "found {} matches to the maharsha dibur hamatchil {} in gemara {}\n".format(num_of_matches, maharsha.encode('utf-8'), daf_amud)
                    log.write(error)
                    print error
                else:
                    search_gemara(text,daf_amud, 3)
            if num_of_matches == 0:
                if diburs == 1 or diburs == 3:
                    search_rashi(text, daf_amud, 0)
                elif diburs == 0:
                    error = "did not find any matches for maharsha dibur hamatchil {} in gemara {}\n".format(maharsha.encode('utf-8'), daf_amud)
                    log.write(error)
                    print error
                elif diburs == 2:
                    search_gemara(text, daf_amud, 1)
            if num_of_matches == 1:
                #Helper.postLink(link("Maharsha on Taanit " + daf_amud , "Taanit " + daf_amud + ":" + str(line)))
                true_find = "matched!! a maharsha DH {} in the gemara daf {} , line {} \n".format(maharsha.encode('utf-8'), daf_amud, line)
                print true_find
                log.write(true_find)

#looks for the marsha's reference in rashi

def search_rashi(text, daf_amud, diburs = 2):
    num_of_matches = 0
    lines = get_lines_number(daf_amud)
    text = re.sub("'", "", text)
    text = replaceAbbrevs(text)
    dibur = re.split(ur'\s', text)
    if diburs == 2:
        maharsha = dibur[3] + " " + dibur[4]
    elif diburs == 3:
        maharsha = dibur[3] + " " + dibur[4] + " " + dibur[5]
    elif diburs == 1:
        maharsha = dibur[3]
    elif diburs == 0:
        maharsha = dibur[4]
    url = 'http://' + Helper.server + '/api/texts/' + 'Rashi_on_Taanit.' + daf_amud + '.' +str(1) + '-' + str(lines)
    response = urllib2.urlopen(url)
    resp = response.read()
    rashi = json.loads(resp)["he"]
    lines = len(rashi)
    for line in range(0, lines):
        for dh in rashi[line]:
            dibur_hamatchil = re.split('-', dh)[0]
            dibur_hamatchil = replaceAbbrevs(dibur_hamatchil)
            if maharsha in dibur_hamatchil:
                num_of_matches += 1
                msg = "found a rashi  match {}  for the maharsha {} in {} , line {} \n".format(dibur_hamatchil.encode('utf-8'), maharsha.encode('utf-8'), daf_amud, line)
                #log.write(msg)
                print msg
        if line == lines - 1:
            if num_of_matches > 1:
                if diburs == 3 or diburs ==0:
                    error = "found {} matches to the maharsha dibur hamatchil {} in Rashi {}, line{}\n".format(num_of_matches, maharsha.encode('utf-8'), daf_amud, line)
                    log.write(error)
                    print error
                else:
                    search_rashi(text, daf_amud, 3)
            if num_of_matches == 0:
                if diburs == 1 or diburs ==3 :
                    search_rashi(text,daf_amud, 0)
                elif diburs == 0:
                    error = "did not find any matches for maharsha dibur hamatchil {} in rashi {}\n".format( maharsha.encode('utf-8'), daf_amud)
                    log.write(error)
                    print error
                elif diburs == 2:
                    search_rashi(text, daf_amud, 1)
            if num_of_matches == 1:
                true_find = "matched!! a maharsha DH {} in the rashi daf {}, line {} \n".format(maharsha.encode('utf-8'), daf_amud, line)
                print true_find
                log.write(true_find)

#looks for the maharsha's reference in tosafot
def search_tosafot(text, daf_amud, diburs = 2):
    text = re.sub("'", "", text)
    dibur = re.split(ur'\s', text)
    if diburs == 2:
        maharsha = replaceAbbrevs(dibur[3]) + " " + replaceAbbrevs(dibur[4])
    elif diburs == 3:
         maharsha = dibur[3] + " " + dibur[4] + " " + dibur[5]
    elif diburs == 1:
        maharsha = replaceAbbrevs(dibur[3])
    #maharsha = replaceAbbrevs(maharsha)
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
            #print "tosafot dibur hamatchil", daf_amud, line, len(dibur), tos, dibur[0]+ " " + dibur[1]
            if maharsha in tos:
                num_of_matches += 1
                msg = "found a Tosafot  match {}  for the maharsha {} in {} , line {} \n".format(tos.encode('utf-8'), maharsha.encode('utf-8'), daf_amud, line)
                #log.write(msg)
                print msg
        if line == lines - 1:
            if num_of_matches > 1:
                if diburs == 3 or diburs ==1:
                    error = "found {} matches to the maharsha dibur hamatchil {} in Tosafot {}\n".format(num_of_matches, maharsha.encode('utf-8'), daf_amud)
                    log.write(error)
                    print error
                    break
                search_tosafot(text, daf_amud, 3)
            if num_of_matches == 0:
                if diburs == 3 or diburs == 1:
                    error = "did not find any matches for maharsha dibur hamatchil {} in Tosafot {}\n".format( maharsha.encode('utf-8'), daf_amud)
                    log.write(error)
                    print error
                    break
                search_tosafot(text, daf_amud, 1)
            if num_of_matches == 1:
                true_find = "matched!! a maharsha DH {} in the Tosafot daf {}, line {} \n".format(maharsha.encode('utf-8'), daf_amud, line)
                print true_find
                log.write(true_find)
                break


# main function, parses the text file lools for reference to rashi or tosafot and calls there functions
def parse_dapim(text):
    shas = 0
    tosafos = 0
    rashi = 0
    amud_num = 'b'
    daf = re.split(ur'@11([^@]*)', text)
    chidushei_halachot = [[],[]]
    DH = []
    for daf_num, content in zip(daf[1::2], daf[2::2]):
        cut_books = re.split(ur'@66([^@]*)', content)
        amudim = re.split(ur'@44ע"ב', cut_books[0])
        for amud in amudim:
            if amud_num == 'b':
                amud_num = 'a'
            else:
                amud_num = 'b'
            halachot = re.split(ur'@44',amud)
            for verse in halachot:
                DH.append(verse)
                number = hebrew.heb_string_to_int(daf_num[3:])
                if ur'רש"י' in verse[0:10]:
                    search_rashi(verse, str(number) + amud_num)
                    rashi +=1
                    pass
                elif ur'תוס' in verse[0:10]:
                    #search_tosafot(verse, str(number) + amud_num)
                    tosafos +=1
                    pass
                else:
                    #search_gemara(verse, str(number) + amud_num)
                    shas +=1
                    pass
            chidushei_halachot.append(halachot)
    print "shas", shas, "rashi", rashi, "tosafot", tosafos
    return chidushei_halachot
    print chidushei_halachot[1][0]

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
    Helper.postText("Maharsha on Taanit", file_text, False)

if __name__ == '__main__':
    text = open_file()
    parsed_text = parse_dapim(text)
    #Helper.createBookRecord(book_record())
    #save_parsed_text(parsed_text)
    #run_post_to_api()


