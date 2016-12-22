# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
#from sefaria.model import *

from functions import *

import pycurl
import cStringIO
import re
import codecs
from bs4 import BeautifulSoup
import sys
sys.setrecursionlimit(10000)

def get_parsed_text():
    soup = url_to_soup("http://www.hebrew.grimoar.cz/vital/saare_kedusa.htm")
    ps = soup.find_all(text=True)
    title_tags = soup.find_all('b')
    titles = []
    for title in title_tags:
        titles.append(remove_html(title.string).strip())
    for title in titles:
        print u"TITLE: "+title+" "+repr(title)
    text = []
    for p in ps:
        if not_blank(p):
            if  not_blank(p[-1])!=True:
                p = p[:-1]
            text.append(p.strip())

    shaar_box = []
    final_text=[]
    for p in ps:
        if p in titles:
            final_text.append(shaar_box)
            shaar_box = []
        shaar_box.append(p)
    final_text.append(shaar_box)

    for index, s in enumerate(final_text):
        for index2, p in enumerate(s):
            print str(index)+" "+str(index2)
            print p,repr(p)




def url_to_soup(url):
    chapter_buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    
    c.setopt(c.WRITEFUNCTION, chapter_buf.write)
    c.perform()
    soup = BeautifulSoup(chapter_buf.getvalue(), 'html.parser')
    return soup;

def remove_html(s):
    #take out html script
    s = re.sub("<.*?>","",s)
    return s;

def not_blank(s):
    return len(re.sub("\w+", "",s))!=0

get_parsed_text()