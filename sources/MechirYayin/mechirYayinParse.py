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
import codecs
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup
import urllib2

def make_perek_array(book):
    tc = TextChunk(Ref(book), "he")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    for index, perek in enumerate(return_array):
        tc = TextChunk(Ref(book+" "+str(index+1)), "he")
        for x in range(len(tc.text)):
            return_array[index].append([])
    return return_array
aleph_mem=u'א-מ'
def post_my_term():
    term_obj = {
        "name": "Mechir Yayin",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Mechir Yayin",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'מחיר יין',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
def post_my_index():
    # create index record
    record = SchemaNode()
    record.add_title('Mechir Yayin on Esther', 'en', primary=True, )
    record.add_title(u'מחיר יין', 'he', primary=True, )
    record.key = 'Mechir Yayin on Esther'

    intro_node = JaggedArrayNode()
    intro_node.add_title('Introduction', 'en', primary = True)
    intro_node.add_title(u'הקדמה', 'he', primary = True)
    intro_node.key = 'Introduction'
    intro_node.depth = 1
    intro_node.addressTypes = ['Integer']
    intro_node.sectionNames = ['Paragraph']
    record.append(intro_node)
    
    #now we add text node
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True
    text_node.depth = 3
    text_node.addressTypes = ['Integer', 'Integer', 'Integer']
    text_node.sectionNames = ['Chapter','Verse','Comment']
    text_node.toc_zoom=2
    record.append(text_node)

    record.validate()

    index = {
        "title": "Mechir Yayin on Esther",
        "base_text_titles": [
          "Esther"
        ],
        "dependence": "Commentary",
        "collective_title": "Mechir Yayin",
        "categories": ['Tanakh','Commentary'],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
        

def make_file():
    response = urllib2.urlopen('https://he.wikisource.org/wiki/%D7%9E%D7%97%D7%99%D7%A8_%D7%99%D7%99%D7%9F')
    with open('text.html', 'w') as f:
        f.write(response.read())
def prep_line(s):
    for match in re.findall(ur'^.*?\.',s):
        if u',' not in match:
            s=s.replace(match,u'<b>'+match+u'</b>')
    return remove_extra_space(s)
def remove_extra_space(s):
    while u'  ' in s:
        s=s.replace(u'  ',u' ')
    s=s.replace(u' .',u'.').replace(u' ,',u',')
    return s
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);      

def parse_mechir(post=True,link=True):
    soup = BeautifulSoup(open('text.html'), "html.parser")
    
    past_start=False
    past_intro=False
    full_text=make_perek_array('Esther')
    intro_box=[]
    perek_box=[]
    pasuk_box=[]
    current_perek=0
    current_pasuk=0
    for line in u' '.join(soup(text=True)).split(u'\n'):
        if u'נו, ראוי לך המעיין שתדע כי כל דבר שי' in line:
            past_start=True
        if u'( ח"ג קנב' in line:
            break
        if past_start and not_blank(line):
            if u'עריכה' in line:
                past_intro=True
            else:
                intro_box.append(remove_extra_space(line))
        if past_intro and not_blank(line):
            if u'עריכה' in line:
                current_perek+=1
            else:
                for pasuk_match in re.findall(ur'^\s*[א-מ]{1,2}\s+',line):
                    current_pasuk=getGematria(pasuk_match)
                    line = line.replace(pasuk_match,u'')
                full_text[current_perek-1][current_pasuk-1].append(prep_line(line))
    """
    for pindex, perek in enumerate(full_text):
        for paindx, pasuk in enumerate(perek):
            for rindex, paragraph in enumerate(pasuk):
                print pindex, paindx, rindex, paragraph 
    """
    if post:
        version = {
            'versionTitle': 'Mechir Yayin, Warsaw 1880',
            'versionSource': 'https://he.wikisource.org/wiki/%D7%9E%D7%97%D7%99%D7%A8_%D7%99%D7%99%D7%9F',
            'language': 'he',
            'text': intro_box
        }
        post_text_weak_connection("Mechir Yayin on Esther, Introduction", version)
    
        version = {
            'versionTitle': 'Mechir Yayin, Warsaw 1880',
            'versionSource': 'https://he.wikisource.org/wiki/%D7%9E%D7%97%D7%99%D7%A8_%D7%99%D7%99%D7%9F',
            'language': 'he',
            'text': full_text
        }
        post_text_weak_connection("Mechir Yayin on Esther", version)
    if link:
        for pindex, perek in enumerate(full_text):
            for paindex, pasuk in enumerate(perek):
                for cindex, comment in enumerate(pasuk):
                    link = (
                            {
                            "refs": [
                                     'Mechir Yayin on Esther, {}:{}:{}'.format(pindex+1, paindex+1, cindex+1),
                                     'Esther {}:{}'.format(pindex+1, paindex+1),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_mechir_yayin_linker"
                            })
                    post_link(link, weak_network=True)
        

#make_file()
#post_my_term()
#post_my_index()
parse_mechir(True,True)