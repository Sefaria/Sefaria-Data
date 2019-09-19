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

def is_start_of_sefer(parasha):
    for starter in he_sefer_names:
        if starter in parasha:
            return starter
    return False
def extract_ref(s):
    if re.search(ur'^@0\[(\S+),\s*(\S+)\]',s):
        return list(map(lambda(x):getGematria(x),re.search(ur'^@0\[(\S+),\s*(\S+)\]',s).group(1,2)))
    return False
def nk_post_index():
    record = SchemaNode()
    record.add_title('Nachal Kedumim on Torah', 'en', primary=True, )
    record.add_title(u'נחל קדומים על תורה', 'he', primary=True, )
    record.key = 'Nachal Kedumim on Torah'


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
        "title":"Nachal Kedumim on Torah",
        "base_text_titles": [
           "Genesis","Exodus","Leviticus","Numbers","Deuteronomy"
        ],
        "dependence": "Commentary",
        "collective_title":"Nachal Kedumim",
        "categories":['Tanakh','Commentary'],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def parse_text(posting=True):
    sfraim_list=[]
    sefer_box=None
    past_start=False
    current_perek=1
    current_pasuk=1
    with open('נחל קדומים מוכן.txt') as myFile:
        lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
    for line in lines:
        if u'@9' in line:
            if is_start_of_sefer(line):
                if sefer_box:
                    sfraim_list.append(sefer_box)
                print is_start_of_sefer(line)
                sefer_box=make_perek_array(en_sefer_names[he_sefer_names.index(is_start_of_sefer(line))])  
                past_start=True
        elif past_start and not_blank(line):  
            if extract_ref(line):
                #print line
                pair=extract_ref(line)
                if pair[1]<current_pasuk and current_perek==pair[0]:
                    #print "BAD PASUK", line, en_sefer_names[len(sfraim_list)]
                    #0/0
                    1/1
                if pair[0]<current_perek:
                    #print "BAD PEREK", line, en_sefer_names[len(sfraim_list)]
                    #0/0
                    1/1
                current_perek=pair[0]
                current_pasuk=pair[1]
            sefer_box[current_perek-1][current_pasuk-1].append(clean_line(line))
    sfraim_list.append(sefer_box)
    #0/0
    if posting:
        for sindex, sefer in enumerate(sfraim_list):
            version = {
                'versionTitle': 'Nachal Kedumim, Warsaw, 1889',
                'versionSource': 'http://beta.nli.org.il/he/books/NNL_ALEPH001156903/NLI',
                'language': 'he',
                'text': sefer
            }
            print "posting "+en_sefer_names[sindex]+" text..."
            post_text_weak_connection('Nachal Kedumim on Torah, '+en_sefer_names[sindex], version)
    return sfraim_list
           
            
def clean_line(s):
    re.sub(ur'^@0\[(\S+),\s*(\S+)\]',u'',s)
    s=s.replace(u'@3',u'<b>').replace(u'@2',u'</b>')
    return s
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
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def make_links():
    textdict=parse_text(False)
    for sindex, sefer in enumerate(en_sefer_names):
        sefer_array = textdict[sindex]
        for perek_index,perek in enumerate(sefer_array):
            for pasuk_index, pasuk in enumerate(perek):
                for comment_index, comment in enumerate(pasuk):
                    link = (
                            {
                            "refs": [
                                     'Nachal Kedumim on Torah, {}, {}:{}:{}'.format(sefer, perek_index+1, pasuk_index+1, comment_index+1),
                                     '{} {}:{}'.format(sefer,perek_index+1, pasuk_index+1),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_nacha_kedumim_linker"
                            })
                    print link.get('refs')
                    post_link(link, weak_network=True)
def post_nk_term():
    term_obj = {
        "name": "Nachal Kedumim",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Nachal Kedumim",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'נחל קדומים',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
    
#post_nk_term()
#nk_post_index()
#parse_text()
make_links()


"""
ל בן צורי שדי. @2פירש רבינו אפרים אמר שמעון אני איש מלחמה ובעל חRANGED
"""