# -*- coding: utf-8 -*-
import os
import re
import sys
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
import codecs
from fuzzywuzzy import fuzz

title_dict = {u"אורח חיים":"Orach Chaim" ,u"יורה דעה":"Yoreh Deah" ,u"אבן העזר":"Even HaEzer",u"חושן משפט":"Choshen Mishpat"} 
title_list = [u"אורח חיים",u"יורה דעה",u"אבן העזר",u"חושן משפט"]
def nb_post_index():
    # create index record
    record = SchemaNode()
    record.add_title('Noda BiYhudah II', 'en', primary=True, )
    record.add_title(u'נודע ביהודה מהדורא תנינא', 'he', primary=True, )
    record.key = 'Noda BiYhudah II'

    # add nodes for chapters
    for section in title_list:
        section_node = JaggedArrayNode()
        section_node.add_title(title_dict[section], 'en', primary=True)
        section_node.add_title(section, 'he', primary=True)
        section_node.key = title_dict[section]
        section_node.depth = 2
        section_node.addressTypes = ['Integer','Integer']
        section_node.sectionNames = ["Teshuva","Paragraph"]
        record.append(section_node)


    record.validate()

    index = {
        "title": "Noda BiYhudah II",
        "categories": ["Responsa"],
        "schema": record.serialize()
    }
    print "posting index..."
    post_index(index,weak_network=True)

def nb_post_text():
    for nb_file in os.listdir("files"):
        if ".txt" in nb_file:
            with open("files/"+nb_file) as myfile:
                lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        responsa_box=[]
        responsas=[]
        for line in lines:
            if "IGNORE" not in line:
                if u"@00" in line:
                    if len(responsa_box)>0:
                        responsas.append(responsa_box)
                        responsa_box=[]
                elif not_blank(line):
                    responsa_box.append(remove_markers(line))
        responsas.append(responsa_box)
        
        version = {
            'versionTitle': 'Noda Bi-Yehudah Part II; Warsaw, 1880',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001983501',
            'language': 'he',
            'text': responsas
        }
        print "posting "+title_dict[highest_fuzz(title_dict.keys(),nb_file.decode('utf8'))]+" text..."
        #post_text('Noda BiYhudah II, '+title_dict[highest_fuzz(title_dict.keys(),nb_file.decode('utf8'))], version,weak_network=True)
        post_text_weak_connection('Noda BiYhudah II, '+title_dict[highest_fuzz(title_dict.keys(),nb_file.decode('utf8'))], version)
        
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def remove_markers(s):
    if u"@22" in s or u"@44" in s:
        s=u"<small>"+s+u"</small>"
    if u"A" in s or u"@01" in s:
        s=u"<b>"+s+u"</b>"
    return re.sub(ur"@\d*",u"",s).replace(u"A",u'')
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match

posting_index=False
posting_text=True

if posting_index:
    nb_post_index()
if posting_text:
    nb_post_text()
