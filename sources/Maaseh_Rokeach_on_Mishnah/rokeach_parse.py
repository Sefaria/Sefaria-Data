# -*- coding: utf-8 -*-
import os
import re
import sys
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
import django
django.setup()
from sources.functions import *
from fuzzywuzzy import fuzz
import data_utilities
import re
import csv
import pycurl
import cStringIO
from bs4 import BeautifulSoup

home_url='https://he.wikisource.org/wiki/%D7%9E%D7%A2%D7%A9%D7%94_%D7%A8%D7%95%D7%A7%D7%97_%D7%A2%D7%9C_%D7%94%D7%9E%D7%A9%D7%A0%D7%94'

mishnah_titles = {}
for tractate_title in library.get_indexes_in_category("Mishnah"):
    he_title = library.get_index(tractate_title).get_title("he")
    mishnah_titles[he_title]=tractate_title
sedarim=[]
for cat in library.get_text_categories():
    if "Seder" in cat and len(cat.split())==2:
        sedarim.append(cat)
        
tractates_by_seder={}
for cat in sedarim:
    tractates_by_seder[cat]=[]
    for title in library.get_indexes_in_category(cat):
        if "Mishnah" in title:
            tractates_by_seder[cat].append(title)
        if "Pirkei" in title:
            tractates_by_seder[cat].append("Mishnah Avot")
#nashim has different orrder than convention in rokeach
tractates_by_seder["Seder Nashim"]=["Mishnah Yevamot","Mishnah Ketubot","Mishnah Kiddushin","Mishnah Gittin","Mishnah Nedarim","Mishnah Nazir","Mishnah Sotah"]
intro_titles=[['Introduction',u'הקדמה'],['Preface',u'פתיחה לשיתא סדרי משנה']]
def url_to_soup(url):
    chapter_buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    
    c.setopt(c.WRITEFUNCTION, chapter_buf.write)
    c.perform()
    soup = BeautifulSoup(chapter_buf.getvalue(), 'html.parser')
    return soup;
def not_blank(s):
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match
def get_tractate_list():
    return_list=[]
    home_soup=url_to_soup(home_url)
    for td in home_soup.find_all('td')[1:]:
        if td.a:
            #print "APPENDING...",td.text,highest_fuzz(mishnah_titles.keys(), td.text)
            return_list.append(highest_fuzz(mishnah_titles.keys(), td.text))
    return return_list
def get_seder(tractate_title):
    for seder in sedarim:
        for tractate in tractates_by_seder[seder]:
            if tractate_title in tractate or tractate in tractate_title:
                return seder
def post_rokeach_index():
    record = SchemaNode()
    record.add_title('Maaseh Rokeach on Mishnah', 'en', primary=True)
    record.add_title(u'מעשה רוקח על המשנה', 'he', primary=True)
    record.key = 'Maaseh Rokeach on Mishnah'
    
    for title_set in intro_titles:
        intro_node = JaggedArrayNode()
        intro_node.add_title(title_set[0], 'en', primary=True)
        intro_node.add_title(title_set[1], 'he', primary=True)
        intro_node.key = title_set[0]
        intro_node.depth = 1
        intro_node.addressTypes = ["Integer"]
        intro_node.sectionNames = ["Paragraph"]
        record.append(intro_node)
        
    tractate_list = get_tractate_list()
    for seder in sedarim:
        seder_node = SchemaNode()
        seder_node.add_title(seder, 'en', primary=True)
        seder_node.add_title(library.get_term(seder).get_titles()[1], 'he', primary=True)
        seder_node.key = seder
        print seder
        for tractate in tractates_by_seder[seder]:
            if library.get_index(tractate).get_title('he') in tractate_list:
                tractate_node = JaggedArrayNode()
                tractate_node.add_title(tractate.replace("Mishnah ",''), 'en', primary=True)
                tractate_node.add_title(library.get_index(tractate).get_title('he').replace(u'משנה ',u''), 'he', primary=True)
                tractate_node.key = tractate.replace("Mishnah ",'')
                tractate_node.depth = 1
                tractate_node.addressTypes = ["Integer"]
                tractate_node.sectionNames = ["Paragraph"]
                seder_node.append(tractate_node)
            else:
                1/1
        record.append(seder_node)
    record.validate()
    
    index = {
        "title":'Maaseh Rokeach on Mishnah',
        "categories":["Kabbalah","Commentary"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def clean_comment_line(s):
    s=s.replace(u'\xa0',u' ')
    s=re.sub(ur'\[.*?\]',u'',s)
    s=re.sub(ur'\d+ *',u'',s)
    s=re.sub(ur'פ"(\S+) מ"(\S+)(?=\))',ur'\1:\2',s)
    s=s.replace(u',,',u',').replace(u'""',u'"').replace(u'(',u'<small>(').replace(u')',u')</small>')
    return s
def post_minshna_comments():
    home_soup=url_to_soup(home_url)
    for td in home_soup.find_all('td')[1:]:
        if td.a:
            english_title=library.get_index(highest_fuzz(mishnah_titles.keys(), td.text)).get_title().replace("Mishnah ","")
            if "Pirkei" in english_title:
                english_title="Avot"
            if True:#"Yev" in english_title:
                print "Posting {}...".format(english_title)
                mesechet_page=url_to_soup('https://he.wikisource.org'+ td.a.get('href'))
                comment_box=[]
                for p in mesechet_page.find_all('p'):
                    if not_blank(p.text):
                        comment_box.append(clean_comment_line(p.text))
                version = {
                    'versionTitle': 'Maaseh Rokeach, Amsterdam 1740',
                    'versionSource': 'https://he.wikisource.org/wiki/%D7%9E%D7%A2%D7%A9%D7%94_%D7%A8%D7%95%D7%A7%D7%97_%D7%A2%D7%9C_%D7%94%D7%9E%D7%A9%D7%A0%D7%94',
                    'language': 'he',
                    'text': comment_box
                }
                post_text_weak_connection("Maaseh Rokeach on Mishnah, {}, {}".format(get_seder(english_title),english_title), version)
def preface_filter(s):
    return (not_blank(s) and u'^' not in s)
def post_introductions():
    intro_urls={'Introduction':'https://he.wikisource.org/wiki/%D7%9E%D7%A2%D7%A9%D7%94_%D7%A8%D7%95%D7%A7%D7%97_%D7%A2%D7%9C_%D7%94%D7%9E%D7%A9%D7%A0%D7%94/%D7%94%D7%A7%D7%93%D7%9E%D7%94',
                "Preface":"https://he.wikisource.org/wiki/%D7%9E%D7%A2%D7%A9%D7%94_%D7%A8%D7%95%D7%A7%D7%97_%D7%A2%D7%9C_%D7%94%D7%9E%D7%A9%D7%A0%D7%94/%D7%A4%D7%AA%D7%99%D7%97%D7%94_%D7%9C%D7%9E%D7%A9%D7%A0%D7%99%D7%95%D7%AA"}
    intro_box=[]
    intro=url_to_soup(intro_urls['Introduction'])
    for p in intro.find_all('p'):
        intro_box.append(clean_comment_line(p.text))
    """
    for line in intro_box:
        print "LINE", line
    0/0    
    """
    intro=url_to_soup(intro_urls['Preface'])
    in_preface=False
    for p in intro.find_all(True):
        if u'כבר כתב הגאון בעל תי"ט' in p.text and not re.search(ur'[A-Za-z]+',p.text):
            preface_box=filter(lambda(x):preface_filter(x),list(map(lambda(x):clean_comment_line(x),p.text.split('\n'))))
            break
    """
    for line in preface_box:
        print "LINE", line
    """
    print "posting intro..."
    version = {
        'versionTitle': 'Maaseh Rokeach, Amsterdam 1740',
        'versionSource': 'https://he.wikisource.org/wiki/%D7%9E%D7%A2%D7%A9%D7%94_%D7%A8%D7%95%D7%A7%D7%97_%D7%A2%D7%9C_%D7%94%D7%9E%D7%A9%D7%A0%D7%94',
        'language': 'he',
        'text': intro_box
    }
    post_text_weak_connection("Maaseh Rokeach on Mishnah, Introduction", version)
    print "posting preface..."
    version = {
        'versionTitle': 'Maaseh Rokeach, Amsterdam 1740',
        'versionSource': 'https://he.wikisource.org/wiki/%D7%9E%D7%A2%D7%A9%D7%94_%D7%A8%D7%95%D7%A7%D7%97_%D7%A2%D7%9C_%D7%94%D7%9E%D7%A9%D7%A0%D7%94',
        'language': 'he',
        'text': preface_box
    }
    post_text_weak_connection("Maaseh Rokeach on Mishnah, Preface", version)

#post_rokeach_index()  
post_minshna_comments()
post_introductions()
