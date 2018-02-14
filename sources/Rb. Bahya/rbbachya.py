# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import re
from sources.functions import *
def find_bugs(files):
    prev_line = ""
    for file in files:
        current_siman = 0
        next_siman = current_siman
        for line in open(file):
            line = line.replace("\r", "").replace("\n", "")
            line_wout_spaces = line.replace(" ", "")
            if len(line_wout_spaces) < 20:
                continue
            poss = line_wout_spaces.split(",")[0]
            if poss.isdigit():
                next_siman = int(poss)
            if next_siman < current_siman:
                print "------------------------"
                print file
                print "{} < {}".format(next_siman, current_siman)
                print prev_line
                print "****"
                print line
            prev_line = line
            current_siman = next_siman


def parse(file):
    current_chapter = 1
    current_verse = 1
    text = {}
    text[current_chapter] = {}
    text[current_chapter][current_verse] = []
    p = re.compile(u"^\d+,\d+\.")
    for line in open(file):
        line = line.replace("\r", "").replace("\n", "")
        line = line.decode('utf-8')
        line_wout_spaces = line.replace(" ", "")
        if len(line_wout_spaces) < 20:
            continue
        match = p.match(line_wout_spaces)
        
        if match:
            next_chapter, next_verse = match.group(0).replace(".","").split(",")
            next_chapter = int(next_chapter)
            next_verse = int(next_verse)
            assert next_chapter >= current_chapter
            current_chapter = next_chapter
            current_verse = next_verse
            if current_chapter not in text:
                text[current_chapter] = {}
            if current_verse not in text[current_chapter]:
                text[current_chapter][current_verse] = []
            first_period = line.find(".")
            line = line[first_period:]
        text[current_chapter][current_verse].append(line)
    return text


def create_schema_and_post(results):
    for book in results:
        for chapter in results[book]:
            results[book][chapter] = convertDictToArray(results[book][chapter])
        results[book] = convertDictToArray(results[book])
    for book in results:
        send_text = {
            "text": results[book],
            "language": "en",
            "versionTitle": "Torah Commentary by Rabbi Bachya ben Asher, trans. Eliyahu Munk, 1998.",
            "versionSource": "http://www.urimpublications.com/Merchant2/merchant.mv?Screen=PROD&Store_Code=UP&Product_Code=ba&Category_Code=bde"
        }
        post_text("Rabbeinu Bahya, {}".format(book), send_text)


if __name__ == "__main__":
    files = ["Bereshit.txt", "Shemot.txt", "Vayikra.txt", "Bamidbar.txt", "Devarim.txt"]
    find_bugs(files)
    results = {}
    for file in files:
        results[file.replace(".txt","")] = parse(file)
    create_schema_and_post(results)