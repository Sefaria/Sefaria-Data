#encoding=utf-8

import django
django.setup()
# import bs4 as bs
# import urllib.requests
import os
import regex as re
import unicodecsv as csv
from sefaria.system.database import db
import unicodedata

from sefaria.model import *
from sefaria.system.database import db
from bs4 import BeautifulSoup, element
from collections import OrderedDict
from sefaria.system.exceptions import InputError
from collections import OrderedDict, Counter
from bs4 import BeautifulSoup, element

import numpy
from time import sleep
import bleach
import shutil
from sources.functions import *
import unicodedata
from sefaria.utils.hebrew import strip_cantillation
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from data_utilities.util import WeightedLevenshtein
import datetime
import traceback

def bs_read(fileName):
    with open(fileName) as f:
        file_content = f.read()

    content = BeautifulSoup(file_content, "lxml")
    headWord = clean_txt(content.findAll('h1')[0].text)
    t = Topic(headWord)
    b = BookCit(u'before')
    wait = True
    for tag in content.findAll():
        if tag.name != 'h1' and wait:
            wait = True
            continue
        wait = False
        if tag.name == 'h2':
            t.citationsBb.append(b)
            b = BookCit(clean_txt(tag.text))
        else:
            txt = clean_txt(tag.text)
            b.cit_list.append(txt)

    if t.citationsBb[0].bookname == 'before':
        for ic, c in enumerate(t.citationsBb[0].cit_list):
            if c == t.headWord:
                # t.citationsBb[0].cit_list.pop(ic)
                pass
            elif re.search(u'ראה', c):
                txt_split = c.split(':')
                t.see = txt_split[1]
    return t

def clean_txt(text):
    cleaned = u' '.join(text.split())
    return cleaned

class BookCit(object):

    def __init__(self, bookname):
        self.bookname = bookname
        self.cit_list = []

class Topic(object):

    def __init__(self, headWord):
        self.headWord = headWord
        self.citationsBb = [] # list of BookCits
        self.see = None
        self.altTitles = None


if __name__ == "__main__":
    topic_le_table = dict()
    with open(u'/home/shanee/www/Sefaria-Data/sources/Aspaklaria/headwords.csv', 'r') as csvfile:
        file_reader = csv.DictReader(csvfile)
        for i, row in enumerate(file_reader):
            pass
            # topic_le_table[row['']] =
    topics = dict()
    for file in os.listdir(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/www.aspaklaria.info/001_ALEF"):
        if u'_' in file:
            continue
        t = bs_read(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/www.aspaklaria.info/001_ALEF/{}".format(file))
        topics[t.headWord] = t