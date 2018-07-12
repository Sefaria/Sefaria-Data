# -*- coding: utf-8 -*-

import argparse
import sys
import helperFunctions as Helper
#from helperFunctions import run_once
import json
import re
import csv
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import difflib
import hebrew


"""def book_record():
    return {
        "title": 'Meshech Hochma',
        "titleVariants": ["Meshech Hochma", "Meir Simcha HaCohen"],
        "heTitle": 'משך חכמה',
        "heTitleVariants" :['משך חכמה', 'מאיר שמחה הכהן'],
        "sectionNames": ["Parsha", "Comment"],
        "categories": ['Parshanut'],
    }"""


def run_parser():
    print "running parser"
    parsed_text = []
    cur_chapter = 1
    cur_verse = 1
    #regex = re.compile(ur'@11(.*)@22',re.UNICODE)
    with open("source/Radak_on_Genesis.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()

    #get rid of some unhelpful markup
    ucd_text = re.sub(ur'@11(.*?)@33', ur'@55\1', ucd_text)
    ucd_text = re.sub(ur'@00([^@]*)\n', '', ucd_text)
    ucd_text = ucd_text.replace(u'@44(שם)@55', u'(שם)')
    #split according to chapter. Will also include the chapter letters in the results.
    chapters = re.split(ur'@22([^@]*)', ucd_text)
    for chapter_num, chapter in zip(chapters[1::2],chapters[2::2]):
        if chapter_num.strip() != '':
            cur_chapter = hebrew.heb_string_to_int(chapter_num.strip())
            parsed_chapter = []
            expand_list_assign(parsed_text, cur_chapter-1, parsed_chapter)
        #now split on verse numbers, capturing the verse numbers as well
        verses = re.split(ur'@44\(([\u0590-\u05ea]{1,2})\)',chapter)
        for verse_num, verse in zip(verses[1::2], verses[2::2]):
            if verse_num.strip() != '':
                parsed_verse = []
                cur_verse = hebrew.heb_string_to_int(verse_num.strip())
                expand_list_assign(parsed_chapter, cur_verse-1, parsed_verse)
            comments = verse.split('@55')[1:]
            for comment in comments:
                if comment.strip() != '':
                    parsed_verse.append(comment)


    pretty_print(parsed_text)
    save_parsed_text(parsed_text)


def expand_list_assign(list, index, value):
    """since we are dealing with a sparse list, we need to grow the list size according to the index"""
    if index > len(list) - 1:
        list.extend([[]] * (index + 1 - len(list)))
    list[index] = value


def pretty_print(parsed_text):
    print "TEXT: ["
    for i, chapter in enumerate(parsed_text,1):
        print "CHAPTER %s[" % i
        for j, verse in enumerate(chapter,1):
            print "VERSE %s[" % j
            if verse is not None:
                for k, comment in enumerate(verse,1):
                    print "[%s]" % comment.encode('utf-8')
            else:
                print "[None]"
            print "]"
        print "]"
    print "] END TEXT"

""" Saves a text to JSON """
def save_parsed_text(text):
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": 'Radak on Genesis',
        "versionTitle": "Presburg : A. Schmid, 1842",
        "versionSource": "http://www.worldcat.org/title/perush-radak-al-ha-torah-sefer-bereshit/oclc/867743220",
        "language": "he",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Radak on Genesis.json", 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api():
    #Helper.createBookRecord(book_record())
    with open("preprocess_json/Radak on Genesis.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Radak on Genesis", file_text, False)


""" The main function, runs when called from the CLI"""
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--preprocess", help="Perform the preprocess and parse the files but do not post them to the db", action="store_true")
    parser.add_argument("-a", "--postapi", help="post data to API",
                    action="store_true")
    parser.add_argument("-l", "--postlinks", help="post links to API",
                    action="store_true")
    args = parser.parse_args()
    #Map command line arguments to function arguments.
    if args.preprocess:
        run_parser()
    if args.postapi:
        print "posting to api"
        run_post_to_api()