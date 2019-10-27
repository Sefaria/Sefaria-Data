# -*- coding: utf-8 -*-
import os
import re
import sys
import csv
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
import django
django.setup()
from sources.functions import *


eng_parshiot_dict = {"Genesis":["Bereshit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach",
"Vayeshev", "Miketz", "Vayigash", "Vayechi"],
                     "Exodus":["Shemot", "Vaera", "Bo", "Beshalach", "Yitro",
"Mishpatim", "Terumah", "Tetzaveh", "Ki Tisa", "Vayakhel", "Pekudei"],
                      "Leviticus":["Vayikra", "Tzav", "Shmini",
"Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar", "Bechukotai"],
                      "Numbers":["Bamidbar", "Nasso","Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei"],
                      "Deuteronomy":["Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo", "Nitzavim", "Vayeilech", "Ha'Azinu",
"V'Zot HaBerachah"]}
he_sefer_names = [u"בראשית",u"שמות",u"ויקרא",u"במדבר", u"דברים"]
en_sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
def ys_post_index():
    record = SchemaNode()
    record.add_title('Yeriot Shlomo on Torah', 'en', primary=True, )
    record.add_title(u'יריעות שלמה על תורה', 'he', primary=True, )
    record.key = 'Yeriot Shlomo on Torah'
    
    intro_node = JaggedArrayNode()
    intro_node.add_title("Introduction", 'en', primary=True, )
    intro_node.add_title(u'הקדמה', 'he', primary=True, )
    intro_node.key = "Introduction"
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
        "title":"Yeriot Shlomo on Torah",
        "base_text_titles": [
           "Genesis","Exodus","Leviticus","Numbers","Deuteronomy"
        ],
        "dependence": "Commentary",
        "collective_title":"Yeriot Shlomo",
        "categories":['Tanakh','Commentary'],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def parse_ys(posting=True, linking=False):
    result_dict={}
    link_dict={}
    with open('Yeriot Shlomo links - fixed.tsv') as my_file:
        reader = csv.reader(my_file, delimiter='\t')
        for sefer in en_sefer_names:
            result_dict[sefer]=make_perek_array(sefer)
            link_dict[sefer]=make_perek_array(sefer)
        current_chapter=0
        current_verse=0
        for row in reader:
            print row[0]
            current_sefer=parasha_to_sefer(re.search(r'(?<=, )\D+(?= )',row[0]).group())
            print re.search(r'(?<=, )\D+(?= )',row[0]).group(), current_sefer
            if row[2]:
                print row[2]
                ref = re.search(r'\d+:\d+:\d+',row[2]).group()
                current_chapter=int(ref.split(':')[0])
                current_verse=int(ref.split(':')[1])
            elif row[3]:
                ref = re.search(r'(?<= )\d+:\d+',row[3]).group()
                current_chapter=int(ref.split(':')[0])
                current_verse=int(ref.split(':')[1])
    
            result_dict[current_sefer][current_chapter-1][current_verse-1].append(clean_line(row[1]))
            if row[2]:
                link_dict[current_sefer][current_chapter-1][current_verse-1].append(row[2])
            elif row[3]:
                link_dict[current_sefer][current_chapter-1][current_verse-1].append(row[3])
                
    for sefer in en_sefer_names:
        for cindex, chapter in enumerate(result_dict[sefer]):
            for vindex, verse in enumerate(chapter):
                for coindex, comment in enumerate(verse):
                    print sefer, cindex, vindex, coindex, comment
            
    if posting:
        for sefer in en_sefer_names:
            version = {
                'versionTitle': "Yeriot Shelomo, Prague 1609",
                'versionSource': 'http://primo.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH001978635&context=L',
                'language': 'he',
                'text': result_dict[sefer]
            }
            #post_text("Yeriot Shlomo on Torah, {}".format(sefer),  version, weak_network=True)
            #0/0
            post_text_weak_connection("Yeriot Shlomo on Torah, {}".format(sefer),  version)
    if linking:
        for sefer in en_sefer_names:
            for cindex, chapter in enumerate(link_dict[sefer]):
                for vindex, verse in enumerate(chapter):
                    for lindex, link in enumerate(verse):
                        link = link.replace('.',':').replace('Mizrachi ','Mizrachi, ')
                        if u'-' in link:
                            link=link.split('-')[0]
                        else:
                            continue
                        link_set = (
                                {
                                "refs": [
                                         'Yeriot Shlomo on Torah, {}, {}:{}:{}'.format(sefer, cindex+1, vindex+1, lindex+1),
                                         link,
                                         ],
                                "type": "commentary",
                                "auto": True,
                                "generated_by": "sterling_yeriot_shlomo_linker"
                                })
                        print link_set.get('refs')
                        post_link(link_set, weak_network=True)
                        if "Rashi" in link:
                            link_set = (
                                    {
                                    "refs": [
                                             'Yeriot Shlomo on Torah, {}, {}:{}:{}'.format(sefer, cindex+1, vindex+1, lindex+1),
                                             ':'.join(link.replace('Rashi on ','').split(':')[:-1]),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_yeriot_shlomo_linker"
                                    })
                            print link_set.get('refs')
                            post_link(link_set, weak_network=True)
                        if "Mizrachi" in link:
                            link_set = (
                                    {
                                    "refs": [
                                             'Yeriot Shlomo on Torah, {}, {}:{}:{}'.format(sefer, cindex+1, vindex+1, lindex+1),
                                             ':'.join(link.replace('Mizrachi, ','').split(':')[:-1]),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_yeriot_shlomo_linker"
                                    })
                            print link_set.get('refs')
                            post_link(link_set, weak_network=True)
                            
                            for a in Ref(link).linkset().array():
                                if "Rashi" in a.refs[0]:
                                    link_set = (
                                            {
                                            "refs": [
                                                     'Yeriot Shlomo on Torah, {}, {}:{}:{}'.format(sefer, cindex+1, vindex+1, lindex+1),
                                                     a.refs[0],
                                                     ],
                                            "type": "commentary",
                                            "auto": True,
                                            "generated_by": "sterling_yeriot_shlomo_linker"
                                            })
                                    print link_set.get('refs')
                                    post_link(link_set, weak_network=True)
                                if "Rashi" in a.refs[1]:
                                    link_set = (
                                            {
                                            "refs": [
                                                     'Yeriot Shlomo on Torah, {}, {}:{}:{}'.format(sefer, cindex+1, vindex+1, lindex+1),
                                                     a.refs[1],
                                                     ],
                                            "type": "commentary",
                                            "auto": True,
                                            "generated_by": "sterling_yeriot_shlomo_linker"
                                            })
                                    print link_set.get('refs')
                                    post_link(link_set, weak_network=True)
    
            
            
        
def post_intro():
    with open('יריעות שלמה.txt') as myFile:
        lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
    intro=[]
    for line in lines:
           if u"ל שם זה נקרא ספר הזה 'יריעות שלמה' גם על שם המחבר" in line:
               intro.append(line.replace(u'@11',u''))
               break
    version = {
        'versionTitle': "Yeriot Shelomo, Prague 1609",
        'versionSource': 'http://primo.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH001978635&context=L',
        'language': 'he',
        'text': intro
    }
    #post_text("Yeriot Shlomo on Torah, {}".format(sefer),  version, weak_network=True)
    #0/0
    post_text_weak_connection("Yeriot Shlomo on Torah, Introduction",  version)
               
def clean_line(s):
    s=s.replace('@11','<b>').replace('@22','</b>')
    return s.decode('utf','replace')
def parasha_to_sefer(parasha):
    for sefer in en_sefer_names:
        for p in eng_parshiot_dict[sefer]:
            if parasha==p:
                return sefer
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
def post_ys_term():
    term_obj = {
        "name": "Yeriot Shlomo",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Yeriot Shlomo",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'יריעות שלמה',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
#post_ys_term()
#ys_post_index()
parse_ys(False, True)
post_intro()