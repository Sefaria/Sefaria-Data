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
import glob
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


def create_index(tractate):
    root=JaggedArrayNode()
    heb_masechet = library.get_index(tractate).toc_contents()['heTitle']
    root.add_title(u"Chiddushei Ramban on "+tractate.replace("_"," "), "en", primary=True)
    root.add_title(u'חידושי רמב"ן על '+heb_masechet, "he", primary=True)
    root.key = 'ramban'
    root.sectionNames = ["Daf", "Comment"]
    root.depth = 2
    root.addressTypes = ["Talmud","Integer"]

    root.validate()

    index = {
        "title": "Chiddushei Ramban on "+tractate.replace("_"," "),
        "categories": ["Commentary2", "Talmud", "Ramban"],
        "schema": root.serialize()
    }
    post_index(index)
    return tractate
'''
perek = 5@.*?2@
daf = 2@.*?\d@
dh = 4@.*?1@
before_dh = 7@.*?4@ or 1@.*?4@

'''
def getInfo(line, errors):
     orig_line = line
     line = line.replace('@2', '2@').replace('@1', '1@').replace('@4', '4@').replace('@7', '7@').replace('@5', '5@').replace('@3', '3@')
     try:
         if line.find('5')>=0:
             perek_info = removeAllStrings(re.findall('5@.*?\d@', line)[0])
         else:
             perek_info = ""
     except:
         errors.write(orig_line+"\n\n")
         perek_info = ""


     try:
         if line.find('2')>=0:
             daf_info = re.findall('2@.*?\d@', line)[0]
         else:
             daf_info = ""
     except:
         errors.write(orig_line+"\n\n")
         daf_info = ""


     try:
         if line.find("4@") >= 0 and line.find('1@') >= 0:
            dh_info = re.findall('4@.*?1@', line)[0]
         elif line.find("4@") >= 0:
            dh_info = re.findall('4@.*', line)[0]
         else:
            dh_info = ""
     except:
        errors.write(orig_line+"\n\n")
        dh_info = ""


     try:
         if line.find('7@')>=0:
           before_dh_info = re.findall('7@.*?4@', line)[0]
         else:
           poss = re.findall('1@.*?4@', line)
           if len(poss)>0:
             before_dh_info = poss[0]
           else:
             before_dh_info = ""
     except:
        errors.write(orig_line+"\n\n")
        before_dh_info = ""


     dh = dh_info.replace("4@","").replace("1@","")
     before_dh = before_dh_info.replace("7@","").replace("1@","").replace("4@","")
     return perek_info, daf_info, dh, before_dh


def getDaf(daf_info):
    daf = daf_info.replace("2@", "").replace("1@","").replace("7@","")
    if daf.find('דף')==-1 and daf.find('ע"')==-1:
         print 'no daf'
         pdb.set_trace()
    first_ayin_aleph = daf.find('ע"א')
    last_ayin_aleph = daf.rfind('ע"א')
    first_ayin_bet = daf.find('ע"ב')
    last_ayin_bet = daf.rfind('ע"ב')
    daf = daf.replace('דף','').replace('ד"ף', '')

    if first_ayin_aleph >= 0 and last_ayin_aleph >= 0 and first_ayin_aleph != last_ayin_aleph:
        daf = 2*getGematria('ע"א') - 1
    elif first_ayin_bet >= 0 and last_ayin_bet >= 0 and first_ayin_bet != last_ayin_bet:
        daf = 2*getGematria('ע"ב')
    elif first_ayin_bet >= 0 and first_ayin_aleph >= 0:
        if first_ayin_aleph < first_ayin_bet:
            daf = 2*getGematria('ע"א')
        else:
            daf = 2*getGematria('ע"ב') - 1
    elif first_ayin_aleph >= 0:
        daf = daf.replace('ע"א', '')
        daf = 2*getGematria(daf) - 1
    elif first_ayin_bet >= 0:
        daf = daf.replace('ע"ב', '')
        daf = 2*getGematria(daf)
    else:
        daf = 2*getGematria(daf)
    return daf


def parse(tractate, errors):
     tractate = tractate.replace(" ", "_")
     prev_daf = 1
     problems = open('problems.txt','w')
     text = {}
     daf = 3
     prev_daf = 3
     dh_dict = {}
     for line in open(tractate+"_complete.txt"):
         orig_line = line
         line = line.replace("\n", "").replace('\x80\xa8\xe2\x80\xa8', '')
         if len(line.replace(' ',''))==0:
             continue

         perek_info, daf_info, dh, before_dh = getInfo(line, errors)
         if len(daf_info) > 0:
            daf = getDaf(daf_info)
         if perek_info.find('@') >= 0 or dh.find('@') >= 0 or before_dh.find('@') >= 0:
            errors.write(orig_line+"\n\n")


         line = line.replace('@2', '2@').replace('@1', '1@').replace('@4', '4@').replace('@7', '7@').replace('@5', '5@').replace('@3', '3@')
         comment_start = line.rfind("1@") if line.rfind("1@") >= 0 else line.rfind("4@")
         comment = line[comment_start+2:].replace("3@","<br>")
         comment = comment.replace(" .", ".")


         comment = removeExtraSpaces(comment)
         dh = removeExtraSpaces(dh)
         before_dh = removeExtraSpaces(before_dh)

         if len(dh) > 0 and dh[0] == ' ':
             dh = dh[1:]

         if len(comment) > 0 and comment[0] == ' ':
             comment = comment[1:]

         if comment.find('@') >= 0:
            errors.write(orig_line+"\n\n")

         if type(daf) is int and daf not in text:
             if daf < prev_daf:
                 print 'daf error'
                 pdb.set_trace()
             text[daf] = []
             dh_dict[daf] = []
             prev_daf = daf
         text[daf].append(before_dh + "<b>" + dh+"</b>"+comment)
         dh_dict[daf].append(dh)

         try:
             comment.decode('utf-8')
             dh.decode('utf-8')
             before_dh.decode('utf-8')
         except:
            pdb.set_trace()
     return text, dh_dict


def post(text, dh_dict, tractate):
     text_array = convertDictToArray(text)
     send_text = {
         "text": text_array,
         "versionTitle": "Chiddushei HaRamban, Jerusalem 1928-29",
         "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001294828",
         "language": "he"
     }
     post_text("Chiddushei Ramban on "+tractate, send_text)
     '''links_to_post = []
     match = Match(in_order=True, min_ratio=80, guess=False, range=True, can_expand=False)
     for daf in sorted(dh_dict.keys()):
         dh_list = dh_dict[daf]
         daf_text = Ref(tractate+" "+AddressTalmud.toStr("en", daf)).text('he').text
         results = match.match_list(dh_list, daf_text, tractate+" "+AddressTalmud.toStr("en", daf))
         for key, value in results.iteritems():
             value = value.replace("0:", "")
             talmud_end = tractate + "." + AddressTalmud.toStr("en", daf) + "." + value
             ramban_end = "Chiddushei_Ramban_on_" + tractate + "." + AddressTalmud.toStr("en", daf) + "." + str(key)
             links_to_post.append({'refs': [talmud_end, ramban_end], 'type': 'commentary', 'auto': 'True', 'generated_by': "ramban"+tractate})
     post_link(links_to_post)
     '''


if __name__ == "__main__":
    global tractate
    global text
    global dh_dict
    global errors
    errors = open("errors", 'w')
    not_yet = True
    until_this_one = "avodah_zarah"
    for file in glob.glob(u"*.txt"):
        errors.write(file+"\n")
        if file.find("_complete") >= 0:
            tractate = file.replace("_complete.txt", "").replace("_", " ").title()
            print file
            if not_yet and file.find(until_this_one) == -1:
                continue
            else:
                not_yet = False
            if not_yet == False:
               #create_index(tractate)
               print 'about to parse'
               text, dh_dict = parse(tractate, errors)
               print 'about to post'
               post(text, dh_dict, tractate)
