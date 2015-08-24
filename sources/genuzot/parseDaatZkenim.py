# -*- coding: utf-8 -*-

import argparse
import sys
import helperFunctions as Helper
# from helperFunctions import run_once
import json
import re
import csv
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import difflib
import hebrew


def book_record():
    return {
        "title": 'Daat Zkenim',
        "titleVariants": ["minchat yehuda baaley hatosfot", "daat zkenim al hatora"],
        "heTitle": 'דעת זקנים',
        "heTitleVariants" :['דעת זקנים בעלי התוספות', 'דעת זקנים על התורה'],
        "sectionNames": ["", ""],
        "categories": ['Commentary'],
    }


def open_file():
    with open("source/daat_zkenim.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
    return ucd_text


### in work
def list_tags(text):
    data = re.findall(r'@[0-9][0-9]', text)
    tags_list = dict((x, data.count(x)) for x in data)
    return tags_list


def run_parser(text):
    parasha_num = 0
    cur_chapter = 1
    cur_verse = 1
    chapters = re.split(ur'@09([^@]*)', text)
    parashot = [[], [], [], [], []]
    for chapter_num, chapter in zip(chapters[1::2], chapters[2::2]):
        if chapter_num.strip() != '':
            cur_chapter = hebrew.heb_string_to_int(chapter_num.strip())
            names = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
            parsed_chapter = []
            if cur_chapter == 1:
                parasha_num += 1
                parasha_name = names[parasha_num - 1]
            expand_list_assign(parashot[parasha_num - 1], cur_chapter - 1, parsed_chapter)
            psukim = re.split(ur'@97([^@]*)', chapter)
            for pasuk_num, pasuk in zip(psukim[1::2], psukim[2::2]):
                if pasuk.strip() != '':
                    parsed_verse = []
                    pasuk_num = re.sub("[\(,\)]", "", pasuk_num)
                    cur_verse = hebrew.heb_string_to_int(pasuk_num.strip())
                    expand_list_assign(parsed_chapter, cur_verse - 1, parsed_verse)
                comments = pasuk.split('@98')[1:]
                for comment in comments:
                    if comment.strip() != '':
                        key = re.split(ur'@87', comment)
                        if len(key) > 1:
                            comment = '<b>' + key[0] + '</b>' + key[1]
                        parsed_verse.append(comment)
    return parashot


def expand_list_assign(list, index, value):
    """since we are dealing with a sparse list, we need to grow the list size according to the index"""
    if index > len(list) - 1:
        list.extend([[]] * (index + 1 - len(list)))
    print index, len(list) - 1
    list[index] = value


""" Saves a text to JSON """

def save_parsed_text(text, book):
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": 'Daat Zkenim on' + book,
        "versionTitle": "Presburg : A. Schmid, 1842",
        "versionSource": "http://www.worldcat.org/title/perush-radak-al-ha-torah-sefer-bereshit/oclc/867743220",
        "language": "he",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Daat_Zkenim_on_" + book + ".json", 'w') as out:
        json.dump(text_whole, out)

def run_post_to_api(book):

    with open("preprocess_json/Daat_Zkenim_on_" + book + ".json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Daat Zkenim on " + book, file_text, False)


""" The main function, runs when called from the CLI"""
if __name__ == '__main__':
    text=open_file()
    #print run_parser(text)[0][0][0][0]
    parsed=run_parser(text)
    Helper.createBookRecord(book_record())
    print book_record()
    for x,name in  enumerate(["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"],0):
        save_parsed_text(parsed[x], name)
        #print "posting "+name
        #run_post_to_api(name)

