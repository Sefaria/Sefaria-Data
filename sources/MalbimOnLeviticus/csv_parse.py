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
import data_utilities
import re
import csv

heb_parshiot = [u"ויקרא", u"צו", u"שמיני", u"תזריע", u"מצורע", u"אחרי מות", u"קדושים", u"אמור", u"בהר",u"בחוקתי"]
eng_parshiot = ["Vayikra", "Tzav", "Shmini","Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar", "Bechukotai"]

def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def post_malbim_index():
    # create index record
    record = SchemaNode()
    record.add_title('Malbim on Leviticus', 'en', primary=True, )
    record.add_title(u'מלבי"ם על ויקרא"', 'he', primary=True, )
    record.key = 'Malbim on Leviticus'
    
    for en_title, he_title in zip(eng_parshiot, heb_parshiot):
        parsha_node = JaggedArrayNode()
        parsha_node.add_title(en_title, 'en', primary=True, )
        parsha_node.add_title(he_title, 'he', primary=True, )
        parsha_node.key = en_title
        parsha_node.depth = 2
        parsha_node.addressTypes = ['Integer','Integer']
        parsha_node.sectionNames = ['Siman','Paragraph']
        record.append(parsha_node)
    
    record.validate()

    index = {
        "title": "Malbim on Leviticus",
        "base_text_titles": [
          "Leviticus"
        ],
        "dependence": "Commentary",
        "collective_title": "Malbim",
        "categories": ['Tanakh','Commentary','Malbim','Torah'],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def post_malbim_text():
    parshiot=[]
    parsha_box=[]
    siman_box=[]
    last_siman=0
    with open('Malbim_Vayikra.csv', 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0]:
                parsha=row[0]
                if len(siman_box)>0:
                    parsha_box.append(siman_box)
                if len(parsha_box)>0:
                    parshiot.append(parsha_box)
                parsha_box=[]
                siman_box=[]
                last_siman=0
            if row[1]!=last_siman and row[1] and len(siman_box)>0:
                parsha_box.append(siman_box)
                if int(row[1])!=int(last_siman)+1:
                    parsha_box.append([])
                siman_box=[]
            siman_box.append(row[3])
            if row[1]:
                last_siman=row[1]
    if len(siman_box)>0:
        parsha_box.append(siman_box)
    if len(parsha_box)>0:
        parshiot.append(parsha_box)
    for pindex, parsha in enumerate(parshiot):
        if  pindex>=2:
            print "posting {} {}...".format(pindex, eng_parshiot[pindex])
            version = {
                'versionTitle': 'VERSION',
                'versionSource': 'https://he.wikisource.org/wiki/%D7%A7%D7%98%D7%92%D7%95%D7%A8%D7%99%D7%94:%D7%94%D7%AA%D7%95%D7%A8%D7%94_%D7%95%D7%94%D7%9E%D7%A6%D7%95%D7%94_%D7%A2%D7%9C_%D7%95%D7%99%D7%A7%D7%A8%D7%90',
                'language': 'he',
                'text': parsha
            }
            post_text_weak_connection("Malbim on Leviticus, "+eng_parshiot[pindex], version)
            #post_text("Malbim on Leviticus, "+eng_parshiot[pindex],  version,weak_network=True)
def link_malbim_text():
    parshiot=[]
    parsha_box=[]
    siman_box=[]
    midrash_links=[]
    last_midrash_links=[]
    last_siman=0
    with open('Malbim_Vayikra.csv', 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0]:
                parsha=row[0]
                if len(siman_box)>0:
                    parsha_box.append(siman_box)
                if len(parsha_box)>0:
                    parshiot.append(parsha_box)
                parsha_box=[]
                siman_box=[]
                last_siman=0
            if row[1]!=last_siman and row[1] and len(siman_box)>0:
                parsha_box.append(siman_box)
                if int(row[1])!=int(last_siman)+1:
                    parsha_box.append([])
                siman_box=[]
            siman_box.append(row[2])
            if row[1]:
                last_siman=row[1]
    if len(siman_box)>0:
        parsha_box.append(siman_box)
    if len(parsha_box)>0:
        parshiot.append(parsha_box)
    for pindex, parsha in enumerate(parshiot):
        for sindex, siman in enumerate(parsha):
            if len(midrash_links)>0:
                last_midrash_links=midrash_links[:]
            midrash_links=[]
            for paindex, paragragh in enumerate(siman):
                for ref in paragragh.split(u';'):
                    if not_blank(ref):
                        #print pindex,sindex, paindex,ref
                        link = (
                                {
                                "refs": [
                                         ref,
                                         'Malbim on Leviticus, {} {}:{}-{}'.format(eng_parshiot[pindex],sindex+1,paindex+1,paindex+len(siman)),
                                         ],
                                "type": "commentary",
                                "auto": True,
                                "generated_by": "sterling_Malbim_linker"
                                })
                        post_link(link, weak_network=True)
                        if not re.search(ur'Leviticus \d+:\d+',ref):
                            midrash_links.append(ref)
            if len(midrash_links)<1 and len(last_midrash_links)>0:
                for x in range(len(last_midrash_links)):
                    link = (
                            {
                            "refs": [
                                     last_midrash_links[x],
                                     'Malbim on Leviticus, {} {}:1-{}'.format(eng_parshiot[pindex],sindex+1,1+len(siman)),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_Malbim_linker"
                            })
                    post_link(link, weak_network=True)
                    
        
#post_malbim_index()
post_malbim_text()
link_malbim_text()
    