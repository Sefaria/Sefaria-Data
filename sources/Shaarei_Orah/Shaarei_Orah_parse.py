# -*- coding: utf-8 -*-
import sys
import os
import cStringIO
import pycurl
from bs4 import BeautifulSoup
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
import re
import codecs

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
    return len(re.sub("\w+", "",s).replace("\n",""))!=0 and s!=u'\xa0'
def get_titles():
    return get_parsed_array()[0]
def get_parsed_text():
    return get_parsed_array()[1]
def get_parsed_array():
    soup = url_to_soup("http://www.hebrew.grimoar.cz/gikatalia/saare_ora.htm")
    ps = soup.find_all(text=True)
    title_tags = soup.find_all('b')
    titles = []
    for title in title_tags[2:]:
        titles.append(remove_html(title.string).strip())
    for title in titles:
            print title
    final_text = []
    section_box = []
    for line in ps:
        if not_blank(line):
            if line.strip() in titles:
                final_text.append(section_box)
                section_box = []
            else:
                section_box.append(line.replace("\n",""))
    final_text.append(section_box)
    for section in final_text:
        print "NEW SECTION!"
        for line in section:
            print "L: "+line
    return [list(map(lambda x: x.replace(":",""),titles)),final_text[1:]]

english_titles= ["Introduction","First Gate, Tenth Sefirah","Second Gate, Ninth Sefirah","Third and Fourth Gates, Seventh and Eight Sefirah","Fifth Gate, Sixth Sefirah","Sixth Gate, Fifth Sefirah","Seventh Gate, Fourth Sefirah","Eight Gate, Third Sefirah","Ninth Gate, Second Sefirah","Tenth Gate, First Sefirah"]
text = get_parsed_text()
titles = get_titles()
for index, title in enumerate(titles):
    print "posting "+english_titles[index]+"..."
    version = {
        'title':"Shaarei Orah",
        'versionTitle': 'Shaarei Orah, grimoar',
        'versionSource': 'http://www.hebrew.grimoar.cz/gikatalia/saare_ora.htm',
        'language': 'he',
        'text': text[index]
    }

    post_text('Shaarei Orah, '+english_titles[index], version, weak_network=True)


    