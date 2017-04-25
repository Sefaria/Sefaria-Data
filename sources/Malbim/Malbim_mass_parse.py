# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
import re
import codecs

def is_text_file(s):
    return ".txt" in s
def parse_all_malbim():
    for file in filter(is_text_file,os.listdir("Malbim_texts"))[8:10]:
        if ".txt" in file:
            get_parsed_text(file.split(" ")[2].replace(".txt",""))


def get_parsed_text(book_name):
    print "NOW PARSING "+book_name
    with codecs.open("Malbim_texts/Malbim on "+book_name+".txt", 'r',encoding="utf") as myfile:
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
    Malbim_array = make_perek_array(book_name)
    Biur_array = make_perek_array(book_name)
        
    for index, perek in enumerate(perek_split):
        #to keep track of whether we're parsing Malbim or Beur, we use "M" or "B"
        for pasuk in perek:
            current_sec = "M"
            pasuk_line = pasuk[0].split(" ")[1]
            pasuk_ref = getGematria(pasuk[0].split(" ")[1])
            for line in pasuk[1:]:
                #print "PASUK: "+str(pasuk_ref-1)+" "+"PASUK LINE: "+pasuk_line+" BOOK: "+book_name
                if u"@22" in line:
                    current_sec="B"
                elif current_sec=="B":
                    Biur_array[index][pasuk_ref-1].append(line)
                else:
                    Malbim_array[index][pasuk_ref-1].append(line)
                    """
                    for comment in split_comments(line):
                        print "MA: "+str(len(Malbim_array[index]))
                        Malbim_array[index][pasuk_ref-1].append(comment)
                    """
    """
    print "THIS IS "+book_name
    print "BIUR!"
    for index, perek in enumerate( Biur_array):
        for index2, pasuk in enumerate( perek):
            for comment in pasuk:
                print str(index)+" "+str(index2)+" "+comment

    print "MALBIM!"
    for index, perek in enumerate( Malbim_array):
        for index2, pasuk in enumerate( perek):
            for comment in pasuk:
                print str(index)+" "+str(index2)+" "+comment
    """
    version = {
        'title': "Malbim Beur Hamilot on "+book_name,
        'versionTitle': 'Malbim on '+book_name+'--Wikisource',
        'versionSource': 'https://he.wikisource.org/wiki/%D7%A7%D7%98%D7%92%D7%95%D7%A8%D7%99%D7%94:%D7%9E%D7%9C%D7%91%D7%99%22%D7%9D_%D7%A2%D7%9C_%D7%94%D7%9E%D7%A7%D7%A8%D7%90',
        'language': 'he',
        'text': Biur_array
        }
    post_text('Malbim Beur Hamilot on '+book_name, version, weak_network=True)
        
    version = {
        'title':"Malbim on "+book_name,
        'versionTitle': 'Malbim on '+book_name+'--Wikisource',
        'versionSource': 'https://he.wikisource.org/wiki/%D7%A7%D7%98%D7%92%D7%95%D7%A8%D7%99%D7%94:%D7%9E%D7%9C%D7%91%D7%99%22%D7%9D_%D7%A2%D7%9C_%D7%94%D7%9E%D7%A7%D7%A8%D7%90',
        'language': 'he',
        'text': Malbim_array
        }
        
    #post_text('Malbim on '+book_name, version, weak_network=True)


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
parse_all_malbim()

"""
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

"""
for file in os.listdir("Malbim_texts"):
    text = file.split(" ")[2].replace(".txt","")
    print "http://draft.sefaria.org/admin/create/commentary-version/Malbim/"+text+"/he/"+file.replace(".txt","")+"/placeholder"

for file in os.listdir("Malbim_texts"):
    if ".txt" in file:
        text = file.split(" ")[2].replace(".txt","")
        print "http://draft.sefaria.org/admin/create/commentary-version/Malbim Beur Hamilot/"+text+"/he/Malbim Beur Hamilt on "+text+"/placeholder"
"""
"""
    version = {
    'title': "Malbim Beur Hamilot on Jonah",
    'versionTitle': 'Malbim on Jonah--Wikisource',
    'versionSource': 'https://he.wikisource.org/wiki/%D7%A7%D7%98%D7%92%D7%95%D7%A8%D7%99%D7%94:%D7%9E%D7%9C%D7%91%D7%99%22%D7%9D_%D7%A2%D7%9C_%D7%94%D7%9E%D7%A7%D7%A8%D7%90',
    'language': 'he',
    'text': Biur_array
    }
    post_text('Malbim Beur Hamilot on Jonah', version, weak_network=True)
    
    version = {
    'title':"Malbim on Jonah",
    'versionTitle': 'Malbim on Jonah--Wikisource',
    'versionSource': 'https://he.wikisource.org/wiki/%D7%A7%D7%98%D7%92%D7%95%D7%A8%D7%99%D7%94:%D7%9E%D7%9C%D7%91%D7%99%22%D7%9D_%D7%A2%D7%9C_%D7%94%D7%9E%D7%A7%D7%A8%D7%90',
    'language': 'he',
    'text': Malbim_array
    }
    
    post_text('Malbim on Jonah', version, weak_network=True)
    """