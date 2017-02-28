# -*- coding: utf-8 -*-
import urllib2
import urllib
from urllib2 import URLError, HTTPError
import json 
import pdb
import glob
import os
import sys

import data_utilities.util
from data_utilities import util, sanity_checks
from data_utilities.sanity_checks import TagTester
from data_utilities.dibur_hamatchil_matcher import *
from sources.functions import *
from sefaria.model import *
from sefaria.model.schema import AddressTalmud


def createIndex(enTitle):
    heTitle = getHebrewTitle(enTitle)

    root = JaggedArrayNode()
    root.add_title("Ritva on "+enTitle, "en", primary=True)
    root.add_title(u'ריטב"א על '+heTitle, "he", primary=True)
    root.key = "Ritva+"+enTitle
    root.sectionNames = ["Daf", "Comment"]
    root.depth = 2
    root.addressTypes = ["Talmud", "Integer"]


    root.validate()

    index = {
        "title": "Ritva on "+enTitle,
        "categories": ["Talmud", "Ritva"],
        "schema": root.serialize()
    }

    post_index(index)


def dealWithDaf(line, current_daf):
    orig_line = line
    line = line.replace(" ", "").replace("\xe2\x80\x9d", '"')
    line = line.replace("@22", "").replace('ע"א','').replace('דף', '').replace('\r', '').replace(' ', '').replace('.', '').replace("\xe2\x80", "").replace("\xac", "").replace("\xaa", "")
    if len(line.replace('ע"ב','').replace(' ','').replace('[', '').replace(']', '').replace('(', '').replace(')', '')) == 0:
        return current_daf + 1
    elif line.find('ע"ב') >= 0:
        line = line.replace('ע"ב', '')
        poss_daf = getGematria(line) * 2
        if poss_daf <= current_daf:
            print 'daf prob'
            pdb.set_trace()
        return poss_daf
    else:
        poss_daf = (getGematria(line) * 2) - 1
        if poss_daf <= current_daf:
            print 'daf prob'
            pdb.set_trace()
        return poss_daf

'''
Objective:  Need to get all the image file names in order, get the encoding, then go through and replace in order
Regular expression will find all occurrences
'''
def getBase64(text):
    found = False
    tags = re.findall("<img.*?>", text)
    for tag in tags:
        first_pos = tag.find('"')
        second_pos = tag.rfind('"')
        filename = tag[first_pos+1:second_pos]
        file = open("eruvin/"+filename+".png")
        data = file.read()
        file.close()
        data = data.encode("base64")
        new_tag = '<img src="data:image/png;base64,'+data+'">'
        text = text.replace(tag, new_tag)
        found = True
    return text, found


def parse(file):
    header = ""
    text = {}
    dhs = {}
    current_daf = 0
    for line in open(file):
        line = line.replace('\n', '')
        if line.find("@22") >= 0:
            end = len(line) if line.find("@11") == -1 else line.find("@11")
            current_daf = dealWithDaf(line[:end], current_daf)
            text[current_daf] = []
        if line.find("@11") >= 0:
            line = line.replace("@11", "").replace("@33", "")
            dh, comment, found_dh = getDHComment(line, file)
            comment, found_img = getBase64(comment)
            if current_daf in dhs:
                dhs[current_daf].append(dh.decode('utf-8'))
            else:
                dhs[current_daf] = []
                dhs[current_daf].append(dh.decode('utf-8'))
            if found_dh == True:
                line = "<b>"+dh+"</b>"+comment
            elif found_img == True:
                line = dh + " " + comment
            if len(header) > 0:
                line = "<b>"+header+"</b><br>"+line
                header = ""
            if found_img == False:
                line = removeAllTags(line)
            text[current_daf].append(line.decode('utf-8'))
        elif line.find("@00") >= 0:
            header = line.replace("@00", "")
    return text, dhs



def getDHComment(each_line, file):
    if file.find("makkot") >= 0:
        if each_line.find(".") > 0:
            dh, comment = each_line.split(".", 1)
            return dh, comment, True
        else:
            first_10, rest = splitText(each_line, 10)
            return first_10, rest, False
    found = True
    words = ["פירוש", "כו'", "פי'", "פירש", "פרוש", "פירשו", "ופירש", "ופרשו", 'פרש"י', "."]
    first_10, rest = splitText(each_line, 10)
    for word in words:
        word = " " + word + " " if word != "." else "."
        if first_10.find(word) >= 0:
            dh, comment = each_line.split(word, 1)
            if word == "כו'" :
                dh += "כו' "
            elif word == ".":
                dh += ". "
            else:
                comment = word + " " + comment
            return dh, comment, True

    return first_10, rest, False



def splitText(text, num_words):
    num_words = num_words if len(text.split(" ")) > 20 else len(text.split(" "))/4
    text_arr = text.split(" ", num_words)
    before = " ".join(text_arr[0:num_words])
    after = text_arr[num_words]
    return before, after


def match_and_link(dhs, masechet):
    def base_tokenizer(str):
        str = re.sub(ur"\([^\(\)]+\)", u"", str)
        word_list = re.split(ur"\s+", str)
        word_list = [w for w in word_list if w]  # remove empty strings
        return word_list
    links = []

    for daf in dhs:
        talmud_text = TextChunk(Ref(masechet+"."+AddressTalmud.toStr("en", daf)), lang="he")
        result = match_ref(talmud_text, dhs[daf], base_tokenizer=base_tokenizer)['matches']
        for count, line in enumerate(result):
            if line is None:
                continue
            Ritva_end = "Ritva on "+masechet+"."+str(AddressTalmud.toStr("en", daf))+"."+str(count+1)
            talmud_end = line.normal()
            links.append({'refs': [Ritva_end, talmud_end], 'type': 'commentary', 'auto': 'True', 'generated_by': masechet+"Ritva"})
    post_link(links)


if __name__ == "__main__":
    versionTitle = {}
    versionTitle['Eruvin'] = 'Chidushi HaRitva, Amsterdam, 1729.'
    versionTitle['Sukkah'] = 'Chiddushei HaRashba, Sheva Shitot, Warsaw, 1883.'
    versionTitle['Berakhot'] = 'Berakhah Meshuleshet, Warsaw, 1863.'
    versionTitle['Moed Katan'] = 'Chidushi HaRitva, Amsterdam, 1729.'
    versionTitle['Yoma'] = 'Chiddushei HaRitva, Berlin, 1860.'
    versionTitle['Megillah'] = 'Kodshei David, Livorno, 1792.'
    versionTitle['Rosh Hashanah'] = 'Chiddushei HaRitva, Königsberg, 1858.'
    versionTitle['Taanit'] = 'Chidushi HaRitva, Amsterdam, 1729.'
    versionTitle['Niddah'] = 'Hidushe ha-Ritba al Nidah; Wien 1868.'
    versionTitle['Makkot'] = 'Hamisha Shitot, Sulzbach 1761. Published by Meshulam Zalman'
    versionTitle['Avodah Zarah'] = "Orian Tlita'i, Salonika, 1758."
    files = ["Moed Katan"]
    not_yet = True
    for file in files:
        createIndex(file)
        print file
        text, dhs = parse(file+".txt")
        text_array = convertDictToArray(text)
        send_text = {
        "text": text_array,
        "language": "he",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001201716",
        "versionTitle": versionTitle[file]
        }
        post_text("Ritva on "+file, send_text)
        match_and_link(dhs, file)
