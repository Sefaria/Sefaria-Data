# -*- coding: utf-8 -*-
import os
import re
import csv
import codecs
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
from sefaria.model import *
from bs4 import BeautifulSoup
from sefaria.utils.hebrew import strip_cantillation

def make_soup(url):
    req = urllib.request.Request(url, headers={'User-Agent' : "Magic Browser"}) 
    con = urllib.request.urlopen(req)
    html = con.read()
    return BeautifulSoup(html, "html5lib")

def get_image(url):
    soup = make_soup(url)
    return soup.find("div", class_="vendor-image").img["src"]

def lookup_shoresh(w, ref):
    # in both - cant
    # only second - cant
    # only first - nikud
    #remove all non-Hebrew non-nikud characters (including cantillation and sof-pasuk)
    w = strip_cantillation(w, strip_vowels=False)
    w = re.sub(r"[A-Za-z׃׀־]", "", w)
    lexicon = "BDB Augmented Strong"
    wf = WordForm().load({"form": w, "refs": re.compile("^" + ref + "$")})
    if wf:
        return [x["headword"] for x in [x for x in wf.lookups if x["lexicon"] == lexicon]]


with codecs.open("EmojiGilla Dictionary.csv", 'rb') as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=',')
    for line in csv_reader:
        hebrew_word = line[0].strip()
        print(hebrew_word)
        emoji_link = line[2].strip()
        perek = line[3].strip()
        pasuk = line[4].strip()
        ref = "Esther {}:{}".format(perek, pasuk)
        shoresh = lookup_shoresh(hebrew_word, ref)
        if os.path.exists("./emojis/{}.png".format(shoresh[0])):
            print("Already have {}; skipping".format(shoresh[0]))
            continue
        image = get_image(emoji_link)
        if shoresh:
            urllib.request.urlretrieve(image, "./emojis/" + shoresh[0] + ".png")
        else:
            print(hebrew_word)
