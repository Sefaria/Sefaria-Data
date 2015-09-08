# -*- coding: utf-8 -*-

import json
import re
import helperFunctions as Helper

def book_record():
    return {
        "title": 'Teshuvot haRambam',
        "titleVariants": ["Teshuvot haRambam", "shut haRambam"],
        "heTitle": 'תשובות הרמב"ם',
        "heTitleVariants" :['תשובות הרמב"ם', 'שו"ת הרמב"ם'],
        "sectionNames": ["teshuva", ""],
        "categories": ['Responsa'],
    }

def open_file():
    with open("source/TeshuvotHarambam-1-.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
    return ucd_text
def run_parser (text):
    corpus=[]
    letters = re.split(ur'(\n\S{1,3}\n)', text)
    for shela_num, shela in zip(letters[1::2], letters[2::2]):
        sheela=[]
        #shela_cut_down = re.split(ur"(תשובה"+ur"|"+ur"שאלה)", shela)
        shela_cut_down = re.split(u'\n\n', shela)
        sheela.append(shela_num)
        #print shela_num
        for x in range (0, len(shela_cut_down)):
            bold_first = re.split(u'(^\S{1,10}\s{1})', shela_cut_down[x])
            #print bold_first[1]
            shela_cut_down[x]= ur'<b>' + bold_first[1] + ur'</b>' + bold_first[2]
            sheela.append(shela_cut_down[x])
        corpus.append(sheela)
    return corpus

def save_parsed_text(text):
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": 'Teshuvot harambam',
        "versionTitle": "Leipzig :  H.L. Shnuis, 1859",
        "versionSource": "http://www.worldcat.org/oclc/233123481",
        "language": "he",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/teshuvot_haRambam.json", 'w') as out:
        json.dump(text_whole, out)

def run_post_to_api():
    with open("preprocess_json/Teshuvot_haRambam.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Teshuvot haRambam", file_text, False)

if __name__ == '__main__':
    text=open_file()
    Helper.createBookRecord(book_record())
    parsed=run_parser(text)
    save_parsed_text(parsed)
    run_post_to_api()
    len(parsed)
    print parsed[0][0]

