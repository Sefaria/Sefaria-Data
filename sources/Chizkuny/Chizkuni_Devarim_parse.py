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

def get_parsed_text():
    with open("Chizkuni_Devarim.txt",'r') as myfile:
        lines = myfile.readlines()
    current_perek = 0
    current_pasuk = 0
    devarim_array = make_perek_array("Devarim")
    for line in lines:
        if "@11" in line:
            current_perek = getGematria(line.replace("@11",""))
        elif "@22" in line:
            current_pasuk = getGematria(line.replace("@22",""))
        else:
            if not_blank(line):
                print line
                devarim_array[current_perek-1][current_pasuk-1].append(line)
                #print "ADDED! " + str(current_perek-1)+" "+str(current_pasuk-1)+" "+str(devarim_array[current_perek-1][current_pasuk-1])
                #print "LAST!" + str(devarim_array[0][0])

    for pindex, perek in enumerate(devarim_array):
        for qindex, pasuk in enumerate(perek):
            for comment in pasuk:
                print str(pindex)+" "+str(qindex)+" "+ comment
    return devarim_array

def make_perek_array(book):
    tc = TextChunk(Ref(book), "he")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    for index, perek in enumerate(return_array):
        tc = TextChunk(Ref(book+" "+str(index+1)), "he")
        for x in range(len(tc.text)):
            return_array[index].append([])
    return return_array

def not_blank(s):
    return (len(s.replace(" ","").replace("\n","").replace("\r","").replace("\t",""))!=0);
book = get_parsed_text()
for pindex, perek in enumerate(book):
    for qindex, pasuk in enumerate(perek):
        for comment in pasuk:
            print str(pindex)+" "+str(qindex)+" "+ comment
version = {
    'versionTitle': 'Chizkuni, new upload',
    'versionSource': 'www.sefaria.org',
    'language': 'he',
    'text': book
}
post_text('Chizkuni, Deuteronomy', version)