# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys
import re
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *


sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud


'''
look for lines with perek, pasuk, and a - and tilde
'''
book = sys.argv[1]

def create_index(eng_title, heb_title):
    commentary = JaggedArrayNode()
    commentary.add_title("Gur Aryeh on "+eng_title, 'en', primary=True)
    commentary.add_title(u"גור אריה על "+heb_title, 'he', primary=True)
    commentary.key = "gur aryeh"+eng_title
    commentary.depth = 3
    commentary.sectionNames = ["Chapter", "Verse", "Paragraph"]
    commentary.addressTypes = ["Integer", "Integer", "Integer"]
    commentary.validate()
    index = {
    "title": "Gur Aryeh on "+eng_title,
    "categories": ["Commentary2", "Tanach", "Torah", book],
    "schema": commentary.serialize()
    }
    post_index(index)

def parse_text():
    file = open(book+".txt")
    probs_file = open("probs_file_"+book+".txt", 'w')
    text = {}
    dh_dict = {}
    curr_perek = 0
    curr_passuk = 0
    for line in file:
        line = line.decode('utf-8')
        line = line.replace("\n", "")
        if len(line) == 0:
            continue
        if line.find("$")>=0:
            continue
        elif line.find("~")>=0 and line.find(u"פרק")>=0:
            perek = re.findall(u'פרק [\u05D0-\u05EA]+', line)[0]
            passuk = re.findall(u'פסוק [\u05D0-\u05EA]+', line)[0]
            perek = perek.replace(u"פרק ", u"")
            poss_perek = getGematria(perek)
            if poss_perek < curr_perek:
                print 'perek prob'
                probs_file.write(line.encode('utf-8'))
                pdb.set_trace()
            passuk = passuk.replace(u"פסוק ", u"")
            poss_passuk = getGematria(passuk)
            if poss_perek > curr_perek:
                curr_perek = poss_perek
                text[curr_perek] = {}
                dh_dict[curr_perek] = {}
                curr_passuk = 0
            if poss_passuk <= curr_passuk:
                print 'passuk prob'
                probs_file.write(line.encode('utf-8'))
                pdb.set_trace()
            curr_passuk = poss_passuk
            text[curr_perek][curr_passuk] = []
            dh_dict[curr_perek][curr_passuk] = []
        elif line.find("~")>=0 and line.find(u"פסוק")>=0:
            passuk = re.findall(u'פסוק [\u05D0-\u05EA]+', line)[0]
            passuk = passuk.replace(u"פסוק ", u"")
            poss_passuk = getGematria(passuk)
            if poss_passuk <= curr_passuk:
                print 'passuk prob'
                probs_file.write(line.encode('utf-8'))
            curr_passuk = poss_passuk
            text[curr_perek][curr_passuk] = []
            dh_dict[curr_perek][curr_passuk] = []
        else:
            first_word = line.split(" ")[0]
            if first_word.find("[")>=0 and first_word.find("]")>=0:
                first_word = first_word.replace("[","").replace("]","")
                line = ' '.join(line.split(" ")[1:])
                dh = line.split(".",1)[0]
                line = line.replace(dh, "<b>"+dh+"</b>")
                dh_dict[curr_perek][curr_passuk].append(dh)
                text[curr_perek][curr_passuk].append(line)
            else:
                curr_len = len(text[curr_perek][curr_passuk])
                try:
                    text[curr_perek][curr_passuk][curr_len-1] += "<br>"+line
                except:
                    pdb.set_trace()
    return (text, dh_dict)

def post(text, dh_dict):
     actual_text = {}
     for perek in text:
         actual_text[perek] = convertDictToArray(text[perek])
     text_to_post = convertDictToArray(actual_text)
     send_text = {"text":text_to_post,
                         "versionTitle":"OYW",
                        "versionSource": "http://mobile.tora.ws/",
                        "language":"he"
                         }
     post_text("Gur Aryeh on "+book, send_text)

     links = []
     for perek in dh_dict:
        for passuk in dh_dict[perek]:


            dh_list = dh_dict[perek][passuk]
            rashi_text = get_text_plus("Rashi on "+book+"."+str(perek)+"."+str(passuk))['he']
            match_out_of_order = Match(in_order=False, min_ratio=85, guess=True, range=True, can_expand=False)
            results = match_out_of_order.match_list(dh_orig_list=dh_list, page=rashi_text, ref_title="Gur Aryeh")
            for dh_pos in results:
                result = results[dh_pos].replace("0:","")
                if result.find('-')>=0:
                    x,y = result.split('-')
                    if int(x)>int(y):
                        pdb.set_trace()
                links.append({
                    "refs": [
                        "Rashi on "+book+"."+str(perek)+"."+str(passuk)+"."+result,
                        "Gur Aryeh on "+book+"."+str(perek)+"."+str(passuk)+"."+str(dh_pos)
                    ],
                    "type": "commentary",
                    "auto": True,
                    "generated_by": "Gur Aryeh on "+book+" linker"})
     	post_link(links)
     	links = []



if __name__ == "__main__":
    heTitle = get_text_plus(book)['heTitle']
    create_index(book, heTitle)
    text, dh_dict = parse_text()
    post(text,dh_dict)
