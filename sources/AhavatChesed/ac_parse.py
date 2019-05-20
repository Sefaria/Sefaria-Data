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


sections=[
    [u'Foreword',u'הקדמה'],
    [u'Introduction',u'פתיחה לעניני מדת החסד'],
    [u'Part I',u'חלק ראשון'],
    [u'Part II',u'חלק שני'],
    [u'Part III',u'חלק שלישי'],
    [u'Epilogue',u'חתימת הספר'],
    [u'Addenda',u'השלמה']
]


def not_blank(s):
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);
def parse_text():
    with open("ahavat_chesed.txt") as myFile:
        lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
    current_section_index=-1
    parts=[2,3,4]
    all_ac_sections={}
    ac_chapter_box=[]
    ac_section_box=[]

    all_nc_sections={}
    nc_chapter_box=[]
    nc_section_box=[]
    for line in lines:
        if not_blank(line):
            if re.search(ur'^(הקדמה|השלמה|חתימת|חלק|פתיחה לע)',line):
                if len(ac_chapter_box)>0:
                    ac_section_box.append(ac_chapter_box)
                    nc_section_box.append(nc_chapter_box)
                if len(ac_section_box)>0:
                    all_ac_sections[sections[current_section_index][0]]=ac_section_box
                    all_nc_sections[sections[current_section_index][0]]=nc_section_box
                current_section_index+=1
                ac_chapter_box=[]
                ac_section_box=[]
                nc_chapter_box=[]
                nc_section_box=[]
            elif current_section_index in parts:
                if re.search(ur'^\s*פרק',line) and len(ac_chapter_box)>0:
                    ac_section_box.append(ac_chapter_box)
                    nc_section_box.append(nc_chapter_box)
                    ac_chapter_box=[]
                    nc_chapter_box=[]
                if re.search(ur'^\(\S{1,3}\)',line):
                    nc_chapter_box.append(line)
                else:
                    ac_chapter_box.append(line)
            else:
                if re.search(ur'^\(\S{1,3}\)',line):
                    nc_section_box.append(line)
                else:
                    ac_section_box.append(line)
    all_ac_sections[sections[current_section_index][0]]=ac_section_box
    all_nc_sections[sections[current_section_index][0]]=nc_section_box

    for key in all_ac_sections.keys():
        """
        if "Part" in key:
            for cindex, chapter in enumerate(all_ac_sections[key]):
                for pindex, paragraph in enumerate(chapter):
                    print key,cindex, pindex, paragraph
        else:
            for pindex, paragraph in enumerate(all_ac_sections[key]):
                print key, pindex, paragraph
        """
        version = {
            'versionTitle': "Ahavat Chesed --  Torat Emet",
            'versionSource': 'http://toratemetfreeware.com/online/f_01815.html',
            'language': 'he',
            'text': all_ac_sections[key]
        }
        print "posting {} text...".format(key)
        #post_text("Ahavat Chesed, "+key, version, weak_network=True)
        post_text_weak_connection("Ahavat Chesed, "+key, version)
def post_ac_index():
    record = SchemaNode()
    record.add_title("Ahavat Chesed", 'en', primary=True)
    record.add_title(u'אהבת חסד', 'he', primary=True)
    record.key = "Ahavat Chesed"
    
    for section in sections:
        section_node = JaggedArrayNode()
        section_node.add_title(section[0], 'en', primary = True)
        section_node.add_title(section[1], 'he', primary = True)
        section_node.key = section[0]
        if "Part" in section[0]:
            section_node.depth = 2
            section_node.addressTypes = ['Integer','Integer']
            section_node.sectionNames = ['Chapter','Paragraph']
            record.append(section_node)
        else:
            section_node.depth = 1
            section_node.addressTypes = ['Integer']
            section_node.sectionNames = ['Paragraph']
            record.append(section_node)
    record.validate()
        
    index = {
        "title":"Ahavat Chesed",
        "categories":["Halakhah"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
    

post_ac_index()
parse_text()