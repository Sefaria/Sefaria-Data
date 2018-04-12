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
import csv
from fuzzywuzzy import fuzz
he_titles_in_order=[]
with open('Kad_Hakemach_Titles_FULL_TRANSLATION.csv','r') as file:
    reader = csv.reader(file)
    title_dict = {row[1].decode('utf8'):row[0] for row in reader}
with open('Kad_Hakemach_Titles_FULL_TRANSLATION.csv','r') as file:
    reader = csv.reader(file)  
    for row in reader:
        print row
        he_titles_in_order.append(row[1].decode('utf8'))
for title in he_titles_in_order:
    print title
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    if highest_ratio<70:
        return None
    return best_match
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);

def khk_index_post():
    record = SchemaNode()
    record.add_title('Kad HaKemach', 'en', primary=True)
    record.add_title(u'כד הקמח', 'he', primary=True)
    record.key = 'Kad HaKemach'
    
    for key in he_titles_in_order:
        title_node = JaggedArrayNode()
        title_node.add_title(title_dict[key], 'en', primary=True)
        title_node.add_title(key, 'he', primary=True)
        title_node.key = title_dict[key]
        if "Introduction" in title_dict[key]:
            title_node.depth=1
            title_node.addressTypes=['Integer']
            title_node.sectionNames=['Section']
        else:
            title_node.depth=2
            title_node.addressTypes=['Integer','Integer']
            title_node.sectionNames=['Section','Paragraph']
        record.append(title_node)
    record.validate()
    
    index = {
        "title":'Kad HaKemach',
        "categories":["Philosophy"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True) 
def khk_text_post():
    with open('כד הקמח מוכן.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    sections={}
    #first parse intro:
    past_start = False
    intro_box = []
    for line in lines:
        if u'ר רבינו בחיי ז׳׳ל' in line:
            past_start=True
        if u"אות האלף" in line:
            break
        elif past_start and not_blank(line):
            intro_box.append(fix_tags(line))
    for line in intro_box:
        print "INTRO",line
    
    sections[u"הקדמה"]=intro_box
            
    section_box=[]
    current_section=''
    past_start = False
    for line in lines:
        if u"@01" in line:
            past_start=True
        if past_start and not_blank(line) and u"@00" not in line:
            if u"@01" in line:
                #first append previous section
                if len(section_box)>0:
                    if parse_title in sections.keys():
                        sections[parse_title].append(section_box)
                    else:
                        sections[parse_title]=[section_box]
                #now set title for next section
                section_box=[]
                parse_title = line.replace(u"@01",u'').strip()
            else:
                section_box.append(fix_tags(line))
    #do last section:
    sections[parse_title]=[section_box]
    
    """
    for key in sections.keys():
        print key
        for paindex, part in enumerate(sections[key]):
            for pindex, paragraph in enumerate(part):
                print paindex, pindex, paragraph
    """
    for key in sections:
        version = {
            'versionTitle': 'Kad HaKemach, Warsaw 1878',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001784725',
            'language': 'he',
            'text': sections[key]
        }
        post_text_weak_connection('Kad HaKemach, '+title_dict[highest_fuzz(title_dict.keys(),key)], version)
        #post_text('Kad HaKemach, '+title_dict[highest_fuzz(title_dict.keys(),key)], version,weak_network=True)
def fix_tags(s):
    s = s.replace(u"@11",u'<b>').replace(u"@33",u"</b>")
    return re.sub(ur"@\d{1,4}",u"",s)
#khk_index_post()
khk_text_post()


###code used for ealier stages of parsing but not for the end stages:
"""
for title in library.get_index('Sefer HaMidot').schema['nodes']:
    if 'titles' in title:
        term_dict[title['titles'][1]['text']]=title['key']
for key in term_dict.keys():
    print key, term_dict[key]
f = open("Kad Hakemach Titles PARTIAL TRANSLATION.csv","w")

#we attempt to match English titles from Rav Nachman's Sefer HaMidot:
term_dict = {}

with open('כד הקמח מוכן.txt') as myfile:
    #lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    lines = myfile.readlines()
titles = []
for line in lines:
    if "@01" in line:
        line = line.replace("@01","")
        if line not in titles:
            titles.append(line)
            if highest_fuzz(term_dict.keys(),line.decode('utf8','replace')):
                f.write(term_dict[highest_fuzz(term_dict.keys(),line.decode('utf8','replace'))])
            f.write(','+line.replace("@01",""))
            #if line.decode('utf8') in term_dict.keys():
            #    f.write(term_dict[line.decode('utf8')])
f.close()

f=open("Kad Hakemach Titles WITH REPEATS.csv","w")
for line in lines:
    if "@01" in line:
        f.write(','+line.replace("@01",""))
f.close()

"""