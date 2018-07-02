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
    soup = url_to_soup("http://www.hebrew.grimoar.cz/vital/pri_ec_chajim.htm")
    ps = soup.find('p')
    title_tags = soup.find_all('b')
    titles = []
    for t in title_tags:
        extracted_title = extract_title(t.find(text=True))
        if extracted_title not in titles:
            titles.append(extracted_title)
    for index, t in enumerate(titles):
        print t+" "+str(index)
    fulltext = ''.join(ps.find_all(text=True))
    line_split = fulltext.split('\n')
    parsed_shaarim = []
    shaar_box = []
    chapter_box = []
    final_text = []

    for line in line_split:
        title = extract_title(line)
        if title in titles:
            shaar_box.append(chapter_box)
            chapter_box = []
            if title not in parsed_shaarim or (u"שער חזרת העמידה" in title and len(shaar_box)==7):
                final_text.append(shaar_box)
                shaar_box = []
                parsed_shaarim.append(title)
        else:
            if not_blank(line):
                chapter_box.append(line)
    shaar_box.append(chapter_box)
    final_text.append(shaar_box)
    #extra index crept in
    del final_text[0]
    del final_text[19][0]
    return final_text

def extract_title(line):
    return line.split("-")[0].strip().replace(":","")
def not_blank(s):
    return len(re.sub("\w+", "",s))!=0 and s != u'\xa0'

def url_to_soup(url):
    chapter_buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    
    c.setopt(c.WRITEFUNCTION, chapter_buf.write)
    c.perform()
    soup = BeautifulSoup(chapter_buf.getvalue(), 'html.parser')
    return soup;


text = get_parsed_text()
for index, shaar in enumerate(text):
    for index2, chapter in enumerate(shaar):
        for index3, paragraph in enumerate(chapter):
            print str(index)+" "+str(index2)+" "+str(index3)
            print paragraph #, repr(paragraph)
english_titles = ["Gate of Prayer", "Gate of Blessings","Gate of Fringes","Gate of Teffilin","Gate of the World of Action","Gate of the Holies","Gate of Songs","Gate of the Recitation of the Shema","Gate of the Silent Prayer","Gate of the Repetition of the Silent Prayer","Gate of Amen Intention","Gate of Confession","Gate of Putting Down the Head","Gate of Reading the Torah","Gate of the Afternoon and Evening Prayers","Gate of the Recitation of the Shema Before Retiring","Gate of the Midnight Prayer","Gate of Conduct While Learning","Gate of the Sabbath","Gate of The New Month, Chanukah, and Purim","Gate of Festival","Gate of Passover","Gate of the Omer Count","Gate of Shavuot","Gate of Rosh Hashana","Gate of the Prayers of Rosh Hashana","Gate of the Shofer","Gate of Yom Kippur","Gate of Sukkot","Gate of Lulav"]
#first post and remove introductions, and then go through the whole list.
version = {
    'versionTitle': 'Pri Etz Chaim',
    'versionSource': 'http://www.hebrew.grimoar.cz/vital/pri_ec_chajim.htm',
    'language': 'he',
    'text': text[0][0]
}
print text[0][0][0]
#post_text_weak_connection('Pri Etz Chaim, Gate of Prayer, Introduction', version)
del text[0][0]

version = {
    'versionTitle': 'Pri Etz Chaim',
    'versionSource': 'http://www.hebrew.grimoar.cz/vital/pri_ec_chajim.htm',
    'language': 'he',
    'text': text[5][0]
}
print text[5][0][0]
#post_text_weak_connection('Pri Etz Chaim, Gate of the Holies, From Second Edition', version)
del text[5]

version = {
    'versionTitle': 'Pri Etz Chaim',
    'versionSource': 'http://www.hebrew.grimoar.cz/vital/pri_ec_chajim.htm',
    'language': 'he',
    'text': text[18]
}
print text[18][0][0]
#post_text_weak_connection('Pri Etz Chaim, Gate of the Sabbath, Introduction', version)
del text[18]

version = {
    'versionTitle': 'Pri Etz Chaim',
    'versionSource': 'http://www.hebrew.grimoar.cz/vital/pri_ec_chajim.htm',
    'language': 'he',
    'text': text[24][0]
}
print text[24][0][0]
#post_text_weak_connection('Pri Etz Chaim, Gate of Rosh Hashana, Introduction', version)
del text[24][0]

#now post regular text
for index, shaar in enumerate(text[14:15]):
    index+=14
    version = {
    'versionTitle': 'Pri Etz Chaim',
    'versionSource': 'http://www.hebrew.grimoar.cz/vital/pri_ec_chajim.htm',
    'language': 'he',
    'text': shaar
    }
    print english_titles[index]
    print shaar[0][0]
    post_text_weak_connection('Pri Etz Chaim, '+english_titles[index], version)



