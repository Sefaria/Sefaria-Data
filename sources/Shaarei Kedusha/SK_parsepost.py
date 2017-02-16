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
    return get_parsed_array()[1]
def get_parsed_hakdama():
    return get_parsed_array()[0][0]
def get_parsed_array():
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
    chelek_box = []
    parsed_cheleks = []
    final_text=[]
    for p in ps:
        if p.strip() in titles:
            chelek_box.append(shaar_box)
            shaar_box = []
            if p.strip() == u'הקדמה':
                parsed_cheleks.append(chelek)
                final_text.append(chelek_box)
                chelek_box = []
            else:
                chelek = p.strip().split(" ")[1]
                if chelek not in parsed_cheleks:
                    parsed_cheleks.append(chelek)
                    final_text.append(chelek_box)
                    chelek_box = []
        elif not re.match(u"[A-Za-z]",p) and len(p)>3:
            shaar_box.append(p.replace("\n",""))
    chelek_box.append(shaar_box)
    final_text.append(chelek_box)
    hakdama = final_text[3]
    print "HAKDAMA!"
    for p in hakdama[0][3:]:
        print p
    final_text = final_text[4:]
    for index, s in enumerate(final_text):
        for index2, p in enumerate(s):
            for index3, para in enumerate(p):
                print str(index)+" "+str(index2)+" "+str(index3)
                print para
    return [hakdama, final_text]



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
    return len(re.sub("\w+", "",s).replace("\n",""))!=0
"""
version = {
    'title':"Shaarei Kedusha",
    'versionTitle': 'Shaarei Kedusha',
    'versionSource': 'http://www.hebrew.grimoar.cz/vital/saare_kedusa.htm',
    'language': 'he',
    'text': get_parsed_hakdama()
    }
    
post_text('Shaarei Kedusha, Introduction', version, weak_network=True)
"""
text = get_parsed_text()
for chelek_num in range(1,5):
    version = {
    'title':"Shaarei Kedusha",
    'versionTitle': 'Shaarei Kedusha',
    'versionSource': 'http://www.hebrew.grimoar.cz/vital/saare_kedusa.htm',
    'language': 'he',
    'text': text[chelek_num-1]
    }
    post_text('Shaarei Kedusha, Part '+str(chelek_num), version, weak_network=True)