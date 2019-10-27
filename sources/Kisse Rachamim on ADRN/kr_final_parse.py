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
import csv

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
def post_kr_index():
    record = JaggedArrayNode()
    record.add_title('Kisse Rachamim on Avot D\'Rabbi Natan', 'en', primary=True, )
    record.add_title(u'כסע רחמים על אבות דרבי נתן', 'he', primary=True, )
    record.key = 'Kisse Rachamim on Avot D\'Rabbi Natan'       
    record.depth = 3
    record.toc_zoom=2
    record.addressTypes = ['Integer','Integer','Integer']
    record.sectionNames = ['Chapter','Paragraph','Comment']

    record.validate()

    index = {
        "title":'Kisse Rachamim on Avot D\'Rabbi Natan',
        "base_text_titles": [
           'Avot D\'Rabbi Natan'
        ],
        "dependence": "Commentary",
        "collective_title":"Kisse Rachamim",
        "categories":['Midrash','Commentary'],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
    
def parse_text(posting=True):
    text_array=make_perek_array('Avot D\'Rabbi Natan')
    with open('edited_files/KisseRachamim_Peirush_links.csv') as csvfile:
      reader = csv.reader(csvfile)
      chapter=1
      paragraph=1
      for row in reader:
          ref_pair=re.search(r'\d+:\d+',row[2]).group().split(':')
          chapter=int(ref_pair[0])
          paragraph=int(ref_pair[1])
          text_array[chapter-1][paragraph-1].append(row[1])
          
    not_started_tosafot=[x for x in range(1,42)]
    with open('edited_files/KisseRachamim_Tosafot_links.csv') as csvfile:
      reader = csv.reader(csvfile)
      chapter=1
      paragraph=1
      for row in reader:
          ref_pair=re.search(r'\d+:\d+',row[2]).group().split(':')
          chapter=int(ref_pair[0])
          paragraph=int(ref_pair[1])
          if chapter in not_started_tosafot:
              text_array[chapter-1][paragraph-1].append(u'<b>תוספות:</b><br>'+row[1].decode('utf','replace'))
              not_started_tosafot.remove(chapter)
          else:
              text_array[chapter-1][paragraph-1].append(row[1].decode('utf','replace'))
    #1/0
    if posting:
        version = {
            'versionTitle': 'Kisse Rahamim, Livorno, 1803',
            'versionSource': 'SOURCE',
            'language': 'he',
            'text': text_array
        }
        print "posting kisse text..."
        if 'local' in SEFARIA_SERVER:
            post_text('Kisse Rachamim on Avot D\'Rabbi Natan',  version,weak_network=True, skip_links=True, index_count="on")
        else:
            post_text_weak_connection('Kisse Rachamim on Avot D\'Rabbi Natan',  version)
    return text_array
def link_kr():
    ta = parse_text(False)
    
    for perek_index,perek in enumerate(ta):
        for paragraph_index, pargraph in enumerate(perek):
            for comment_index, comment in enumerate(pargraph):
                link = (
                        {
                        "refs": [
                                 'Kisse Rachamim on Avot D\'Rabbi Natan {}:{}:{}'.format(perek_index+1, paragraph_index+1, comment_index+1),
                                 'Avot D\'Rabbi Natan {}:{}'.format(perek_index+1, paragraph_index+1),
                                 ],
                        "type": "commentary",
                        "auto": True,
                        "generated_by": "sterling_nacha_kedumim_linker"
                        })
                print link.get('refs')
                post_link(link, weak_network=True)
def post_kr_term():
    term_obj = {
        "name": "Kisse Rachamim",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Kisse Rachamim",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'כסע רחמים',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
#post_kr_term()
#post_kr_index()
#parse_text()
link_kr()