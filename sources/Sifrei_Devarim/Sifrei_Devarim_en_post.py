# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *
from fuzzywuzzy import fuzz

sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
#from sefaria.model import *
from functions import *
import re
#if int(line)-last_piska!=1:
#print "ERROR@ "+line
#if len(piskas)!=int(line):
#    print "ERROR@@ "+line
def get_parsed_text():
    return parse_text()[0]
def get_perek_index():
    return parse_text()[1]
def get_parsha_index():
    return parse_text()[2]
def parse_text():
    with open("Sifrei_Devarim_en.txt", 'r') as myfile:
        text_temp = myfile.readlines()
    text = []
    for line in text_temp:
        if is_line(line):
            text.append(re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', line))
    piska_box = []
    piskas = []
    for line in text:
        if re.match(r"[0-9]+",line):
            if len(piska_box) != 0:
                piskas.append(piska_box)
                piska_box = []
                last_piska = int(line)
        elif line.replace("\t","")[0]=="(":
            piska_box.append(line)
    piskas.append(piska_box)
    
    #make perek table, where first entry is perek and second entry is Piska INDEX where the perek starts
    perek_index = []
    last_perek = 0
    for index, part in enumerate(piskas):
        for indexp, p in enumerate(part):
            perek_pasuk = get_perek_pasuk(p)
            print perek_pasuk
            print str(index)+" @"+str(indexp)+" "+p
            if perek_pasuk[0]>0 and perek_pasuk[0]!=last_perek:
                perek_index.append([perek_pasuk[0], piskas.index(part)+1])
                if index>0:
                    perek_index[-2]=[perek_index[-2][0],perek_index[-2][1],piskas.index(part)]
                last_perek = perek_pasuk[0]
    perek_index[-1]=[perek_index[-1][0],perek_index[-1][1],len(piskas)]
    for entry in perek_index:
        print entry

    #make parsha index

    pre_parsha_index = []
    parsha_index = []
    for line in text:
        if not re.match(r"[0-9]+",line) and line.replace("\t","")[0]!="(" and line!="\n" and line[0]!="\t":
            pre_parsha_index.append([get_sefaria_english_parsha(line).replace("\n",""),text[text.index(line)+1]])
    for index, parsha_record in enumerate(pre_parsha_index):
        if index != len(pre_parsha_index)-1:
            parsha_index.append([parsha_record[0],parsha_record[1].replace("\n",""),str(int(pre_parsha_index[index+1][1])-1)])
        else:
            parsha_index.append([parsha_record[0],parsha_record[1].replace("\n",""),len(piskas)])
    for parsha in parsha_index:
        print "PARSHA! "+parsha[0]+" "+str(parsha[1])+" "+str(parsha[2])
        print heb_parshiot[eng_parshiot.index(parsha[0])]
    return [piskas,perek_index,parsha_index]

def is_line(s):
    if "PAGE" in s:
        return False
    return True
def get_perek_pasuk(s): #return array of chapter/pasuk indices. If ibid, returns -1. If there is no index, returns 0,0.
    if re.findall("(?<=\t\(Devarim, )Ibid.+:",s):
        return [-1,-1]
    return list(map(lambda(x): int(x),re.findall("(?<=\t\(Devarim )[0-9]+:[0-9]+",s)[0].split(":"))) if re.findall("(?<=\t\(Devarim )[0-9]+:[0-9]+",s) else [0,0]
def get_sefaria_english_parsha(parsha_name):
    highest_ratio=0
    return_title = 0
    for sefaria_parsha_name in eng_parshiot:
        if fuzz.ratio(parsha_name,sefaria_parsha_name)>highest_ratio:
            return_title=sefaria_parsha_name
            highest_ratio=fuzz.ratio(parsha_name,sefaria_parsha_name)
    return return_title


text = get_parsed_text()
version = {
    'versionTitle': 'Sifrei Devarim, English',
    'versionSource': '(missing)',
    'language': 'en',
    'text': text
    }
#post_text_weak_connection('Sifrei Devarim', version)

