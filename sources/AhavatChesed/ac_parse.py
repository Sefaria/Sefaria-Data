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

nc_sections=[
    [u'Introduction',u'פתיחה לעניני מדת החסד'],
    [u'Part I',u'חלק ראשון'],
    [u'Part II',u'חלק שני'],
    [u'Part III',u'חלק שלישי'],
]
part_i_sections=[[u'Laws of Loans',u'דיני מצות הלואה'],
    [u'Laws of Pledges',u'דין ענייני העבוט'],
    [u'Laws of Wages',u'דיני תשלומי שכר שכיר']]
go_with_next=[u'דין עניני העבוט',u'דיני מצות הלואה'u'דיני תשלומי שכר שכיר בזמנו']
ur'^(דיני מצות הלואה|דין עניני העבוט|דיני תשלומי שכר שכיר בזמנו)'
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
    
    goes_in_next=[]
    for line in lines:
        if not_blank(line):
            if re.search(ur'^(הקדמה|השלמה|חתימת|חלק|פתיחה לע)',line):
                if len(ac_chapter_box)>0:
                    ac_section_box.append(ac_chapter_box)
                    nc_section_box.append(nc_chapter_box)
                if len(ac_section_box)>0:
                    all_ac_sections[sections[current_section_index][0]]=ac_section_box
                    if "Part" in sections[current_section_index][0] or "Introduction" in sections[current_section_index][0]:
                        all_nc_sections[sections[current_section_index][0]]=nc_section_box
                current_section_index+=1
                ac_chapter_box=[]
                ac_section_box=[]
                nc_chapter_box=[]
                nc_section_box=[]
            elif current_section_index in parts:
                if is_new_chapter(line) and len(ac_chapter_box)>0:
                    ac_section_box.append(ac_chapter_box)
                    nc_section_box.append(nc_chapter_box)
                    ac_chapter_box=[]
                    nc_chapter_box=[]
                if re.search(ur'^(דיני מצות הלואה|דין עניני העבוט|דיני תשלומי שכר שכיר בזמנו)',line):
                    goes_in_next.append(u'<b>'+clean_ac_line(line)+u'</b>')
                elif re.search(ur'^\(\S{1,3}\)',line):
                    nc_chapter_box.append(clean_nc_line(line))
                elif re.search(ur'^ובו ',line):
                    ac_chapter_box[-1]=ac_chapter_box[-1]+u' '+clean_ac_line(line)
                else:
                    if len(goes_in_next)>0:
                        ac_chapter_box.append(goes_in_next.pop()+u'<br>'+clean_ac_line(line))
                    else:
                        ac_chapter_box.append(clean_ac_line(line))
            else:
                if re.search(ur'^\(\S{1,3}\)',line):
                    nc_section_box.append(clean_nc_line(line))
                elif re.search(ur'^ובו ',line):
                    ac_section_box[-1]=ac_section_box[-1]+u' '+clean_ac_line(line)
                else:
                    ac_section_box.append(clean_ac_line(line))
    all_ac_sections[sections[current_section_index][0]]=ac_section_box
    all_nc_sections[sections[current_section_index][0]]=nc_section_box
    
    #fix error
    all_nc_sections[sections[2][0]]=all_nc_sections[sections[2][0]][1:]
    _remove=u'םן \.'
    for key in all_ac_sections.keys():
        if "Part" in key:
            clone=all_ac_sections[key][:]
            for cindex, chapter in enumerate(clone):
                for pindex, paragraph in enumerate(chapter):
                    for match in re.findall(ur'\(([^'+_remove+ur']{1,2})\)',paragraph):
                        print match
                    print re.sub(ur'\(([^'+_remove+ur']{1,2})\)',ur'<i data-commentator=\"Netiv Chesed\" data-order=\"\1\"></i>',paragraph)
    """
    if "Part" in key:
        for cindex, chapter in enumerate(all_ac_sections[key]):
            for pindex, paragraph in enumerate(chapter):
                print key,cindex, pindex, paragraph
    else:
        for pindex, paragraph in enumerate(all_ac_sections[key]):
            print key, pindex, paragraph
    0/0
    """
    0/0
    if False:
        for key in all_ac_sections.keys():
            if key=='Part I':
                sects=[['Laws of Loans',0,6],
                    ['Laws of Pledges ',6,8],
                    ['Laws of Wages',9,11]]
                for sect in sects:
                    sect_list=all_ac_sections[key][sect[1]:sect[2]]
                    #"""
                    for x in range(sect[1]):
                        sect_list.insert(0,[])
                    if 'Wages' in sect[0]:
                        sect_list.pop(0)
                    #"""
                    for cindex, chapter in enumerate(sect_list):
                        for pindex, paragraph in enumerate(chapter):
                            print sect[0],cindex, pindex, paragraph
                    version = {
                        'versionTitle': "Ahavat Chesed --  Torat Emet",
                        'versionSource': 'http://toratemetfreeware.com/online/f_01815.html',
                        'language': 'he',
                        'text': sect_list
                    }
                    print "posting ","Ahavat Chesed, {}, {}...".format(key,sect[0])
                    #post_text("Ahavat Chesed, {}, {}".format(key,sect[0]), version, weak_network=True)
                    #post_text("Ahavat Chesed, {}, {}".format(key,sect[0]), version, index_count="off", skip_links=True)
                    #post_text_weak_connection("Ahavat Chesed, {},{}".format(key,sect[0]), version)
                    
                #now post intro to wages...
                version = {
                    'versionTitle': "Ahavat Chesed --  Torat Emet",
                    'versionSource': 'http://toratemetfreeware.com/online/f_01815.html',
                    'language': 'he',
                    'text': all_ac_sections[key][8]
                }
                print "posting {} \"Ahavat Chesed, Laws of Wages, Introduction\" text...".format(key)
                #post_text("Ahavat Chesed, Part I, Laws of Wages, Introduction", version, weak_network=True)
                post_text_weak_connection("Ahavat Chesed, Part I, Laws of Wages, Introduction", version)
            else:
                #1/1
                #"""
                version = {
                    'versionTitle': "Ahavat Chesed --  Torat Emet",
                    'versionSource': 'http://toratemetfreeware.com/online/f_01815.html',
                    'language': 'he',
                    'text': all_ac_sections[key]
                }
                print "posting {} Ahavat Chesed text...".format(key)
                #post_text("Ahavat Chesed, "+key, version, weak_network=True)
                post_text_weak_connection("Ahavat Chesed, "+key, version)
                #"""
    if True:
        for key in all_nc_sections.keys():
            """
            if "Part" in key:
                for cindex, chapter in enumerate(all_ac_sections[key]):
                    for pindex, paragraph in enumerate(chapter):
                        print key,cindex, pindex, paragraph
            else:
                for pindex, paragraph in enumerate(all_ac_sections[key]):
                    print key, pindex, paragraph
            """
            if key=='Part I':
                sects=[['Laws of Loans',0,6],
                    ['Laws of Pledges ',6,8],
                    ['Laws of Wages',9,11]]
                for sect in sects:
                    sect_list=all_nc_sections[key][sect[1]:sect[2]]
                    #"""
                    for x in range(sect[1]):
                        sect_list.insert(0,[])
                    if 'Wages' in sect[0]:
                        sect_list.pop(0)
                    #"""
                    for cindex, chapter in enumerate(sect_list):
                        for pindex, paragraph in enumerate(chapter):
                            print "NC",sect[0],cindex, pindex, paragraph
                    version = {
                        'versionTitle': "Ahavat Chesed --  Torat Emet",
                        'versionSource': 'http://toratemetfreeware.com/online/f_01815.html',
                        'language': 'he',
                        'text': sect_list
                    }
                    print "posting ","Netiv Chesed on Ahavat Chesed, {}, {}...".format(key,sect[0])
                    #post_text("Ahavat Chesed, {}, {}".format(key,sect[0]), version, weak_network=True)
                    #post_text("Netiv Chesed on Ahavat Chesed, {}, {}".format(key,sect[0]), version, index_count="off", skip_links=True)
                    post_text_weak_connection("Ahavat Chesed, {},{}".format(key,sect[0]), version)
                    
                #now post intro to wages...
                version = {
                    'versionTitle': "Ahavat Chesed --  Torat Emet",
                    'versionSource': 'http://toratemetfreeware.com/online/f_01815.html',
                    'language': 'he',
                    'text': all_nc_sections[key][8]
                }
                print "posting {} \"Netiv Chesed on Ahavat Chesed, Laws of Wages, Introduction\" text...".format(key)
                #post_text("Ahavat Chesed, Part I, Laws of Wages, Introduction", version, weak_network=True)
                post_text_weak_connection("Netiv Chesed on Ahavat Chesed, Part I, Laws of Wages, Introduction", version)
            else:
                version = {
                    'versionTitle': "Ahavat Chesed --  Torat Emet",
                    'versionSource': 'http://toratemetfreeware.com/online/f_01815.html',
                    'language': 'he',
                    'text': all_nc_sections[key]
                }
                print "posting {} Netiv Chesed text...".format(key)
                #post_text("Ahavat Chesed, "+key, version, weak_network=True)
                post_text_weak_connection("Netiv Chesed on Ahavat Chesed, "+key, version)
def post_ac_index():
    record = SchemaNode()
    record.add_title("Ahavat Chesed", 'en', primary=True)
    record.add_title(u'אהבת חסד', 'he', primary=True)
    record.key = "Ahavat Chesed"
    
    for section in sections:
        if section[0]=='Part I':
            section_node=SchemaNode()
            section_node.add_title(section[0], 'en', primary = True)
            section_node.add_title(section[1], 'he', primary = True)
            section_node.key = section[0]
            for segment in part_i_sections:
                if 'Wages' in segment[0]:
                    segment_node = SchemaNode()
                    segment_node.add_title(segment[0], 'en', primary = True)
                    segment_node.add_title(segment[1], 'he', primary = True)
                    segment_node.key = segment[0]
                    
                    intro_node = JaggedArrayNode()
                    intro_node.add_title('Introduction', 'en', primary = True)
                    intro_node.add_title(u'פתיחה', 'he', primary = True)
                    intro_node.key = 'Introduction'
                    intro_node.depth = 1
                    intro_node.addressTypes = ['Integer']
                    intro_node.sectionNames = ['Paragraph']
                    segment_node.append(intro_node)
                    
                    text_node = JaggedArrayNode()
                    text_node.key = "default"
                    text_node.default = True
                    text_node.depth = 2
                    text_node.addressTypes = ['Integer', 'Integer']
                    text_node.sectionNames = ['Chapter','Paragraph']
                    segment_node.append(text_node)
                else:
                    segment_node = JaggedArrayNode()
                    segment_node.add_title(segment[0], 'en', primary = True)
                    segment_node.add_title(segment[1], 'he', primary = True)
                    segment_node.key = segment[0]
                    segment_node.depth = 2
                    segment_node.addressTypes = ['Integer','Integer']
                    segment_node.sectionNames = ['Chapter','Paragraph']
                section_node.append(segment_node)
            record.append(section_node)
                    
        else:
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
def post_nc_term():
    term_obj = {
        "name": "Netiv Chesed",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Netiv Chesed",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'נתיב חסד',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
def post_nc_index():
    record = SchemaNode()
    record.add_title("Netiv Chesed on Ahavat Chesed", 'en', primary=True)
    record.add_title(u'נתיב חסד על אהבת חסד', 'he', primary=True)
    record.key = "Netiv Chesed on Ahavat Chesed"
    
    for section in nc_sections:
        if section[0]=='Part I':
            section_node=SchemaNode()
            section_node.add_title(section[0], 'en', primary = True)
            section_node.add_title(section[1], 'he', primary = True)
            section_node.key = section[0]
            for segment in part_i_sections:
                if 'Wages' in segment[0]:
                    segment_node = SchemaNode()
                    segment_node.add_title(segment[0], 'en', primary = True)
                    segment_node.add_title(segment[1], 'he', primary = True)
                    segment_node.key = segment[0]
                    
                    intro_node = JaggedArrayNode()
                    intro_node.add_title('Introduction', 'en', primary = True)
                    intro_node.add_title(u'פתיחה', 'he', primary = True)
                    intro_node.key = 'Introduction'
                    intro_node.depth = 1
                    intro_node.addressTypes = ['Integer']
                    intro_node.sectionNames = ['Paragraph']
                    segment_node.append(intro_node)
                    
                    text_node = JaggedArrayNode()
                    text_node.key = "default"
                    text_node.default = True
                    text_node.depth = 2
                    text_node.addressTypes = ['Integer', 'Integer']
                    text_node.sectionNames = ['Chapter','Paragraph']
                    segment_node.append(text_node)
                else:
                    segment_node = JaggedArrayNode()
                    segment_node.add_title(segment[0], 'en', primary = True)
                    segment_node.add_title(segment[1], 'he', primary = True)
                    segment_node.key = segment[0]
                    segment_node.depth = 2
                    segment_node.addressTypes = ['Integer','Integer']
                    segment_node.sectionNames = ['Chapter','Paragraph']
                section_node.append(segment_node)
            record.append(section_node)
        else:
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
        "title":"Netiv Chesed on Ahavat Chesed",
        "base_text_titles": [
          'Ahavat Chesed'
        ],
        "dependence": "Commentary",
        "collective_title":"Netiv Chesed",
        "categories":["Halakhah","Commentary"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def is_new_chapter(line):
    if re.search(ur'^\s*פרק',line):
        return True
    if u'פתיחה לתשלומי שכר שכיר' in line:
        return True
def clean_ac_line(line):
    line = re.sub(ur'[A-Za-z]',u'',line)
    if re.search(ur'^\s*פרק',line):
        line = u'<b>'+line+u'</b>'
    """<i data-commentator="Sheilat Shalom" data-label="*" data-order="{}"></i>"""
    return line
def clean_nc_line(line):
    line = re.sub(ur'[A-Za-z]',u'',line)
    return line

#post_ac_index()
#parse_text()

#post_nc_term()
#post_nc_index()
parse_text()