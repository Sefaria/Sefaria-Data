# -*- coding: utf-8 -*-
import json
import re
import helperFunctions as Helper
from helperFunctions import run_once
import os
import os.path
import xml.etree.cElementTree as ET


def run_parser():
    files = [230001, 230002, 230003, 230004, 230005]
    book_name = 'BenIshChai'
    corpus = []
    for file in files:
        file_name = 'source/' + str(file) + '.xml'
        print file
        book_tree = ET.parse(file_name)
        tree_root = book_tree.getroot()
        benishchai_text = parse_book(tree_root)
        corpus = corpus + benishchai_text
    save_parsed_text(book_name, corpus)


def parse_book(root):
    all_chaps = []
    for chap_num, chapter_node in enumerate(root.findall('chap'), 1):
        print "chapter ", chap_num, ": ", chapter_node.get('n').encode('utf-8')
        chapter = chapter_node.get('n').encode('utf-8')
        letters = []
        all_chaps.append(letters)
        letters.append(chapter)
        comments = chapter_node.find('./p/d').text.encode('utf-8')
        for x in re.split(r'<ps>', comments):
            x = re.sub('<[^<]+?>', '', x)
            if x != '':
                letters.append(x)
    return all_chaps


""" Saves a text to JSON """


def save_parsed_text(book_name, text):
    print "hello"
    text_whole = {
        "title": book_name,
        "versionTitle": "On Your Way",
        "versionSource": "http://mobile.tora.ws/",
        "language": "he",
        "text": text,
    }
    # save
    Helper.mkdir_p("preprocess_json/Ben Ish Chai")
    with open("preprocess_json/Ben Ish Chai/" + book_name + ".json", 'w') as out:
        json.dump(text_whole, out)
    post_to_api(book_name)


def post_to_api(book_name):
    index_rec =  {
        "title": 'Ben Ish Chai',
        "titleVariants": ["Ben Ish Chai"],
        "heTitle": 'בן איש חי',
        "heTitleVariants" :['בן איש חי', 'רבי יוסף חיים מבגדאד'],
        "sectionNames": ["Parsha", "Comment"],
        "categories": ['Parshanut'],
    }
    Helper.createBookRecord(index_rec)
    dir_name = 'preprocess_json/Ben Ish Chai'
    with open(dir_name + "/" + book_name + ".json", 'r') as filep:
        file_text = filep.read()
    Helper.postText(index_rec["title"], file_text, False)






if __name__ == "__main__":
    print "running parser for Ben Ish Chai"
    run_parser()


