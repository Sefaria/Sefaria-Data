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
import re

def not_blank(s):
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);
def clean_line(s):
    s=s.replace(u'\n',u'')
    if s[-1]!=u':':
        s=s+u":"
    s=re.sub(r'\$(\S+)#',r'<small>[רמז \1]</small>',s)
    s=re.sub(r'%(.*?)#',r'<small>\1</small>',s)
    if re.search(r'&\S+\"\S+#',s):
        s=re.sub(r'[&#]',u'',s)
        s=u'<small>'+s+u'</small>'
    return s
def post_mord_index(tractate):
    record = SchemaNode()
    record.add_title('Mordechai on {}'.format(tractate), 'en', primary=True)
    record.add_title(u'מרדכי על {}'.format(library.get_index(tractate).get_title('he')), 'he', primary=True)
    record.key = 'Mordechai on {}'.format(tractate)
    
    #now we add text node
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True
    text_node.depth = 2
    text_node.addressTypes = ['Integer', 'Integer']
    text_node.sectionNames = ['Chapter', 'Paragraph']
    record.append(text_node)
    
    hagaha_node = JaggedArrayNode()
    hagaha_node.add_title('Hagahot Mordechai', 'en', primary=True)
    hagaha_node.add_title(u'הגהות מרדכי', 'he', primary=True)
    hagaha_node.key = 'Hagahot Mordechai'
    hagaha_node.depth = 1
    hagaha_node.addressTypes = ["Integer"]
    hagaha_node.sectionNames = ["Paragraph"]
    record.append(hagaha_node)
    
    remez_nodes =SchemaNode()
    for remez_ref in get_alt_remez(): 
        print remez_ref
        """
        remez_node = ArrayMapNode()
        remez_node.add_title(remez["English Title"], "en", primary=True)
        remez_node.add_title(remez["Hebrew Title"], "he", primary=True)
        #remez_node.includeSections = True
        remez_node.depth = 1
        remez_node.addressTypes = ['Integer']
        remez_node.sectionNames=["Vav"]
        remez_node.wholeRef = "Sefer Yereim, "+str(remez_range["Starting Index"][0]+1)+":"+str(remez_range["Starting Index"][1]+1)\
            +"-"+str(remez_range["Ending Index"][0]+1)+":"+str(remez_range["Ending Index"][1]+1)
        subref_list=[]
        for vav in remez_range["Vavim"]:
            subref_list.append("Sefer Yereim, "+str(vav["Start Vav"][0]+1)+":"+str(vav["Start Vav"][1]+1)\
            +"-"+str(vav["End Vav"][0]+1)+":"+str(vav["End Vav"][1]+1))
        remez_node.refs = subref_list
        remez_nodes.append(remez_node)
        
        
        remez_node = ArrayMapNode()
        remez_node.wholeRef = "Midrash Lekach Tov on Torah, {}".format(remez['wholeRef'])
        remez_node.includeSections = True
        remez_node.key = remez['sharedTitle']
        remez_node.depth=0
        remez_node.add_shared_term(remez['sharedTitle'])
        remez_nodes.append(remez_node)
        """
    0/0
    record.validate()
    
    index = {
        'base_text_titles': [
        tractate
        ],
        'title': "Mordechai on {}".format(tractate),
        'categories': [
        "Talmud",
        "Bavli",
        "Commentary",
        "Mordechai"
        ],
        'authors': [
        "Mordechai"
        ],
        'dependence': "Commentary",
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def parse_text(posting=True):
    with open("mordechay bk.txt") as myfile:
        lines = list(map(lambda(x): x.decode('utf8', 'replace'), myfile.readlines()))
    prakim=[]
    perek_box=[]
    link_list=[]
    for line in lines:
        for p in line.split(': '):
            if not_blank(p):
                if re.search(ur'%.*?#',p):
                    print re.search(ur'%.*?#',p).group()
                perek_box.append(clean_line(p))
        if u'סליק פ' in line:
            prakim.append(perek_box)
            perek_box=[]
    """
    for pindex, perek in enumerate(prakim):
        for paindex, paragraph in enumerate(perek):
            print pindex, paindex, paragraph
    """
    hagahot=[]
    for chapter in prakim[10:]:
        for paragraph in chapter:
            hagahot.append(paragraph)
    if posting:
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': prakim[:10]
        }
        post_text_weak_connection("Mordechai on Bava Kamma", version)
        #post_text("Modechai on Bava Kamma", version)
    
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': hagahot
        }
        post_text_weak_connection("Mordechai on Bava Kamma, Hagahot Modechai", version)
        #post_text("Modechai on Bava Kamma, Hagahot Modechai", version)
    return prakim
def link_talmud_sections():
    link_list=[]
    prakim = parse_text(False)
    for cindex, chapter in enumerate(prakim[:10]):
        for pindex, paragraph in enumerate(chapter):
            if re.search(ur'\[[^\]]+דף.*?\]',paragraph):
                print re.search(ur'\[[^\]]+דף.*?\]',paragraph).group()
            #link_list.append()
def get_alt_remez():
    remez_map=[]
    prakim=parse_text(False)
    for cindex, chapter in enumerate(prakim[:10]):
        for pindex, paragraph in enumerate(chapter):
            for match in re.findall(ur'\[רמז.*?\]',paragraph):
                remez_map.append([cindex+1,pindex+1,getGematria(match.replace(ur'רמז',ur''))])
    return remez_map
   
post_mord_index("Bava Kamma")
#parse_text(False)
#get_alt_remez()
"""
from file:
        
        מקרא קודים
        # - סוגר קוד קודם ומחזיר לפונט רגיל
        $ - אותיותיות חלוקה בתוך הטקסט פונט שונה וגדול יותר)
        % - מקורות בתוך הטקסט (פונט קטן יותר ושונה]
        & - פונט שונה בתוך הטקסט (מרובע וגדול), ולפעמים גם של תחילת קטע (עם חלון).
        ^ - הגהות מרדכי. לא חלק מהטקסט הראשי אלא תוספת לטקסט כמובלעות.
        < כותרות גדולות, בעיקר ככותרות לפני תחילת פרקים.
"""


    