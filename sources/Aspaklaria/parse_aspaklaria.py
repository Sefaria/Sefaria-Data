#encoding=utf-8

import django
django.setup()
# import bs4 as bs
# import urllib.requests
import os
import regex as re
from sefaria.system.database import db
import unicodedata
import string

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
from sources.functions import *
import unicodecsv as csv


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
    t.citationsBb.append(b)

    tanakh = []
    if t.citationsBb[0].bookname == 'before':
        for ic, c in enumerate(t.citationsBb[0].cit_list):
            if c == t.headWord:
                pass
            elif re.search(u'ראה', c) and re.search(u':', c):
                txt_split = c.split(':')
                see = re.sub(u"[\(\)]", u'', txt_split[1]).split(u',')
                t.see = [re.sub(re.escape(string.punctuation), u'', s) for s in see]
                # t.see = [re.sub(, u'', s) for s in see]
            else:
                tanakh.append(c)
    t.citationsBb.pop(0)
    if tanakh and t.citationsBb:
        t.citationsBb[0] = BookCit(u'Tanakh')
        t.citationsBb[0].cit_list = tanakh

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
            fieldnames = file_reader.fieldnames
            topic_le_table[row[u'he']] = row[u'en']
    all_topics = dict()
    for letter in os.listdir(u'/home/shanee/www/Sefaria-Data/sources/Aspaklaria/www.aspaklaria.info/'):
        if not os.path.isdir(u'/home/shanee/www/Sefaria-Data/sources/Aspaklaria/www.aspaklaria.info/{}'.format(letter)):
            continue
        i = 0
        topics = dict()
        for file in os.listdir(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/www.aspaklaria.info/{}".format(letter)):
            if u'_' in file:
                continue
            if file[:-5].isalpha():
                continue
            t = bs_read(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/www.aspaklaria.info/{}/{}".format(letter, file))
            i+=1
            topics[i] = t
            # topics[topic_le_table[clean_txt(t.headWord.replace(u"'", u"").replace(u"-", u""))]] = t
        letter_name = re.search(u".*_(.*?$)", letter)
        if letter_name:
            letter_name = letter_name.group(1)
            print u'{} headwords in the letter {}'.format(i, letter_name)
        all_topics[letter_name] = topics
    print u'done'