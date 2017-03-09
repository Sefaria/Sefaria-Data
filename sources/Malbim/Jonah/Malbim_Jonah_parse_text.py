# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from functions import *
import re
import codecs

def get_parsed_text():
    with codecs.open("Malbim on Jonah.txt", 'r',encoding="cp1255") as myfile:
        text = myfile.readlines()
    perek_split = []
    perek_box = []
    pasuk_box = []
    for line in text:
        if "@00" in line:
            if len(perek_box) != 0:
                perek_box.append(pasuk_box)
                pasuk_box = []
                perek_split.append(perek_box)
                perek_box =[]
        else:
            if "@11" in line and len(pasuk_box) != 0:
                perek_box.append(pasuk_box)
                pasuk_box = []
            pasuk_box.append(line)
    perek_box.append(pasuk_box )
    perek_split.append(perek_box)

    #there are two seperate commentaries here, each one is returned as its own array.
    Malbim_array = make_perek_array("Jonah")
    Biur_array = make_perek_array("Jonah")

    for index, perek in enumerate(perek_split):
        print "THIS IS A NEW PEREK"
        for pasuk in perek:
            pasuk_ref = getGematria(pasuk[0].split(" ")[1])
            print "PREF: "+pasuk[0].split(" ")[1]
            print "PNUM:"+ str(pasuk_ref-1)
            for line in pasuk[1:]:
                Malbim_array[index][pasuk_ref-1].append(re.sub("<br>", "",line))
    print "MALBIM!"
    for index, perek in enumerate( Malbim_array):
        for index2, pasuk in enumerate( perek):
            for comment in pasuk:
                print str(index)+" "+str(index2)+" "+comment

    version = {
    'title':"Malbim on Jonah",
    'versionTitle': 'Malbim on Jonah--Wikisource',
    'versionSource': 'https://he.wikisource.org/wiki/%D7%A7%D7%98%D7%92%D7%95%D7%A8%D7%99%D7%94:%D7%9E%D7%9C%D7%91%D7%99%22%D7%9D_%D7%A2%D7%9C_%D7%94%D7%9E%D7%A7%D7%A8%D7%90',
    'language': 'he',
    'text': Malbim_array
    }
    
    post_text('Malbim on Jonah', version, weak_network=True)
    
    return perek_split
    
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
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);

def split_comments(s):
    return_array = []
    comments = s.split("<b>")
    for comment in comments:
        if not_blank(comment) and "br" not in comment:
            return_array.append("<b>"+comment)
    return return_array

book = make_perek_array("Jonah")
for index, perek in enumerate(book):
    print "Perek "+str(index+1)+" has "+str(len(book[index]))+" pasukim"

for index, perek in enumerate(get_parsed_text()):
    print "Perek: "+str(index+1)
    for index2, pasuk in enumerate(perek):
        print "P: "+str(index2)
        for comment in pasuk:
            print comment

"""
book = make_perek_array("Jonah")
for index, perek in enumerate(book):
    print "Perek "+str(index+1)+" has "+str(len(book[index]))+" pasukim"
"""