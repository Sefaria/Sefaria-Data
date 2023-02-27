# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import django
django.setup()
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys
import re
import glob

from linking_utilities.dibur_hamatchil_matcher import *

from local_settings import *
from sources.functions import *
from sources.Match import match
from sefaria.model import *
from sefaria.model.schema import AddressTalmud


def create_index(tractate, moed):
    root=JaggedArrayNode()
    heb_masechet = library.get_index(tractate).toc_contents()['heTitle']
    root.add_title(u"Chiddushei Ramban on "+tractate.replace("_"," "), "en", primary=True)
    root.add_title(u'חידושי רמב"ן על '+heb_masechet, "he", primary=True)
    root.key = 'ramban'
    root.sectionNames = ["Daf", "Comment"]
    root.depth = 2
    root.addressTypes = ["Talmud", "Integer"]

    root.validate()

    index = {
        "title": "Chiddushei Ramban on "+tractate.replace("_"," "),
        "categories": ["Talmud", "Bavli", "Commentary", "Ramban", "Seder "+moed],
        "schema": root.serialize(),
        "dependence": "Commentary",
        "base_text_titles": [tractate],
    }
    post_index(index, server=SEFARIA_SERVER)
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


def getDaf(daf_info, daf):
    if daf_info.find('2@ע"ב') >= 0 or daf_info.find('2@ ע"ב') >= 0:
        return daf+1
    daf = daf_info.replace("2@", "").replace("1@","").replace("7@","").strip()
    daf = " ".join(daf.split()[0:3])
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


def preparse(lines):
    new_lines = []
    temp = ""
    for line in lines:
        line = line.replace("@3", "3@").replace("@2", "2@").replace("@6", "6@").replace("\n", "")
        while line.startswith(" "):
            line = line[1:]
        if not line:
            continue
        if "2@" in line:
            temp = line + " "
            pass #starting DH
        elif "3@" in line:
            temp += "<br/>" + line
        elif "6@" in line:
            temp += line + " "
            new_lines.append(temp)
            temp = ""
        else:
            temp += line + " "
    return new_lines




def parse(tractate, errors):
     tractate = tractate.replace(" ", "_")
     prev_daf = 1
     problems = open('problems.txt','w')
     text = {}
     daf = 3
     prev_daf = 3
     dh_dict = {}
     lines = list(open("new/"+tractate+".txt"))
     lines = preparse(lines)
     for line in lines:
         orig_line = line
         line = line.replace("\n", "").replace('\x80\xa8\xe2\x80\xa8', '')
         if len(line.replace(' ','')) == 0:
             continue

         line = line.replace("6@", "")
         perek_info, daf_info, dh, before_dh = getInfo(line, errors)
         if len(daf_info) > 0:
            daf = getDaf(daf_info, daf)
         if perek_info.find('@') >= 0 or dh.find('@') >= 0 or before_dh.find('@') >= 0:
            errors.write(orig_line+"\n\n")


         line = line.replace('@2', '2@').replace('@1', '1@').replace('@4', '4@').replace('@7', '7@').replace('@5', '5@').replace('@3', '3@')
         comment_start = line.rfind("1@") if line.rfind("1@") >= 0 else line.rfind("4@")
         if comment_start < 0:
             comment_start = 0
         else:
             comment_start += 2
         comment = line[comment_start:].replace("3@","")
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
             text[daf] = []
             dh_dict[daf] = []
             prev_daf = daf

         if dh:
             text[daf].append(before_dh + "<b>" + dh+"</b> "+comment)
             dh_dict[daf].append(dh)
         else:
            text[daf].append(comment)


         comment.decode('utf-8')
         dh.decode('utf-8')
         before_dh.decode('utf-8')
     return text, dh_dict


def post(text, dh_dict, tractate):
     text_array = convertDictToArray(text)
     send_text = {
         "text": text_array,
         "versionTitle": "Chiddushei HaRamban, Jerusalem 1928-29",
         "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001294828",
         "language": "he"
     }
     post_text("Chiddushei Ramban on "+tractate, send_text, server=SEFARIA_SERVER)
     links_to_post = []
     for daf in sorted(dh_dict.keys()):
         dh_list = [el.decode('utf-8') for el in dh_dict[daf] if el]
         daf_text = Ref(tractate + " " + AddressTalmud.toStr("en", daf)).text('he')
         results = match_ref(daf_text, dh_list, lambda x: x.split())
         for match_n, match in enumerate(results["matches"]):
             if match:
                 talmud_end = "Chiddushei Ramban on "+tractate + " " + AddressTalmud.toStr("en", daf) + ":" + str(match_n+1)
                 links_to_post.append({'refs': [talmud_end, match.normal()], 'type': 'commentary', 'auto': 'True',
                                       'generated_by': "ramban" + tractate})
     print len(links_to_post)
     post_link(links_to_post, server=SEFARIA_SERVER)
     # for daf in sorted(dh_dict.keys()):
     #     dh_list = [el.decode('utf-8') for el in dh_dict[daf] if el]
     #     daf_text = TextChunk(Ref(tractate+" "+AddressTalmud.toStr("en", daf)), lang='he')
     #     results = match_ref(daf_text, dh_list, lambda x: x)
     #     if not results:
     #         continue
     #     for which_n, result in enumerate(results["matches"]):
     #         if result:
     #             comm_ref = result.normal()
     #             base_ref = tractate+" "+AddressTalmud.toStr("en", daf)+":"+str(which_n+1)
     #             links_to_post.append({'refs': [comm_ref, base_ref], 'type': 'commentary', 'auto': 'True', 'generated_by': "ramban"+tractate})
     # print links_to_post
     # post_link(links_to_post)



if __name__ == "__main__":
    global tractate
    global text
    global dh_dict
    global errors
    errors = open("errors", 'w')
    these = {"Shevuot": "Nezikin", "Megillah": "Moed", "Niddah": "Tahorot",
             "Chullin": "Kodashim"}
    these = {"Niddah": "Tahorot"}
    for file in glob.glob(u"new/*.txt"):
        errors.write(file+"\n")
        tractate = file.replace(".txt", "").replace("new/", "").title()
        print tractate
        create_index(tractate, these[tractate])
        print 'about to parse'
        text, dh_dict = parse(tractate, errors)
        print 'about to post'
        #post(text, dh_dict, tractate)
