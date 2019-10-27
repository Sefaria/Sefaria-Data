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

he_sefer_names = [u"בראשית",u"שמות",u"ויקרא",u"במדבר", u"דברים"]
en_sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
intro_node_titles=[
    ['Title',u'שער'],
    ['Introduction',u'הקדמה']
]

def from_heb_name_to_eng_name(s):
    if isinstance(s, str):
        s=s.decode('utf','replace')
    for nindex, name in enumerate(he_sefer_names):
        if name in s:
            return en_sefer_names[nindex]
def mt_post_index():
    record = SchemaNode()
    record.add_title('Minei Targuma on Torah', 'en', primary=True, )
    record.add_title(u'מיני תרגומא על תורה', 'he', primary=True, )
    record.key = 'Minei Targuma on Torah'

    for title in intro_node_titles:
        intro_node = JaggedArrayNode()
        intro_node.add_title(title[0], 'en', primary=True, )
        intro_node.add_title(title[1], 'he', primary=True, )
        intro_node.key = title[0]
        intro_node.depth = 1
        intro_node.addressTypes = ['Integer']
        intro_node.sectionNames = ['Paragraph']
        record.append(intro_node)
        
    for en_sefer, he_sefer in zip(en_sefer_names, he_sefer_names):
        sefer_node = JaggedArrayNode()
        sefer_node.add_title(en_sefer, 'en', primary=True, )
        sefer_node.add_title(he_sefer, 'he', primary=True, )
        sefer_node.key = en_sefer
        sefer_node.depth = 3
        sefer_node.toc_zoom = 2
        sefer_node.addressTypes = ['Integer', 'Integer','Integer']
        sefer_node.sectionNames = ['Chapter','Verse','Comment']
        record.append(sefer_node)
    
    record.validate()

    index = {
        "title":"Minei Targuma on Torah",
        "base_text_titles": [
           "Genesis","Exodus","Leviticus","Numbers","Deuteronomy"
        ],
        "dependence": "Commentary",
        "collective_title":"Minei Targuma",
        "categories":['Tanakh','Commentary'],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def parse_text(posting=True):
    sefer_dict={}
    for sefer in en_sefer_names:
        sefer_dict[sefer]=make_perek_array(sefer)
    past_start=False
    with open('Minei Targuma - Minei Targuma.tsv') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        chapter=1
        verse=1
        current_sefer=None
        for row in reader:
            #print row[0]
            if 'בראשית' in row[0]:
                print "PS"
                past_start=True
            if past_start:
                if not_blank(row[0]):
                    current_sefer=from_heb_name_to_eng_name(row[0])
                if not_blank(row[1]):
                    chapter=getGematria(row[1].split(',')[0])
                    verse=getGematria(row[1].split(',')[1])
                if not_blank(row[2]):
                    print chapter, verse
                    print row[2]
                    sefer_dict[current_sefer][chapter-1][verse-1].append(row[2])
    #0/0
    if posting:
        for sefer in en_sefer_names:
            version = {
                'versionTitle': 'Vilna, 1836',
                'versionSource': 'https://beta.nli.org.il/he/books/NNL_ALEPH001857234/NLI',
                'language': 'he',
                'text': sefer_dict[sefer]
            }
            print "posting "+sefer+" text..."
            post_text_weak_connection('Minei Targuma on Torah, '+sefer, version)
    return sefer_dict
           
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
def not_blank(s):
    if isinstance(s, str):
        s=s.decode('utf','replace')
    while u" " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def make_links():
    textdict=parse_text(False)
    for sefer in en_sefer_names:
        sefer_array = textdict[sefer]
        for perek_index,perek in enumerate(sefer_array):
            for pasuk_index, pasuk in enumerate(perek):
                for comment_index, comment in enumerate(pasuk):
                    link = (
                            {
                            "refs": [
                                     'Minei Targuma on Torah, {}, {}:{}:{}'.format(sefer, perek_index+1, pasuk_index+1, comment_index+1),
                                     '{} {}:{}'.format(sefer,perek_index+1, pasuk_index+1),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_minei_targuma_linker"
                            })
                    print link.get('refs')
                    post_link(link, weak_network=True)
                    
                    
                    link = (
                            {
                            "refs": [
                                     'Minei Targuma on Torah, {}, {}:{}:{}'.format(sefer, perek_index+1, pasuk_index+1, comment_index+1),
                                     'Onkelos {} {}:{}'.format(sefer,perek_index+1, pasuk_index+1),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_minei_targuma_onkelos_linker"
                            })
                    print link.get('refs')
                    post_link(link, weak_network=True)
def post_intros():
    with open('Minei Targuma - Minei Targuma.tsv') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        intro_box=[]
        for row in reader:
            if not_blank(row[0]):
                if 'הקדמה' in row[0]:
                    version = {
                        'versionTitle': 'Vilna, 1836',
                        'versionSource': 'https://beta.nli.org.il/he/books/NNL_ALEPH001857234/NLI',
                        'language': 'he',
                        'text': intro_box
                    }
                    post_text_weak_connection('Minei Targuma on Torah, Title', version)
                    intro_box=[]
                if 'בראשית' in row[0]:
                    version = {
                        'versionTitle': 'Vilna, 1836',
                        'versionSource': 'https://beta.nli.org.il/he/books/NNL_ALEPH001857234/NLI',
                        'language': 'he',
                        'text': intro_box
                    }
                    post_text_weak_connection('Minei Targuma on Torah, Introduction', version)
                    break
            intro_box.append(row[2])
                
                
def post_mt_term():
    term_obj = {
        "name": "Minei Targuma",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Minei Targuma",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'מיני תרגומא',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
    
#post_mt_term()
#mt_post_index()
#parse_text()
#make_links()
post_intros()

"""
ל בן צורי שדי. @2פירש רבינו אפרים אמר שמעון אני איש מלחמה ובעל חRANGED
"""