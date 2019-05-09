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

name_dict={}
for text in library.get_indexes_in_category('Tanakh'):
    name_dict[library.get_index(text).get_title('he')]=text
prophet_list=[]
    for text in library.get_indexes_in_category('Prophets'):
        prophet_list.append(text)

def file_name_to_sefer(file_name):
    for name in name_dict.keys():
        if name in file_name.decode('utf8','replace'):
            return name
two_sefers=[u'שמואל',u'מלכים']
class megilah:
    def __init__(self, file_name):
        print file_name
        self.file_name = 'files/{}'.format(file_name)
        self.he_name = file_name_to_sefer(file_name)
        self.en_name = name_dict[self.he_name]
        self.has_intro=self.intro_check()
    def intro_check(self):
        with open(self.file_name) as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        for line in lines:
            if not_blank(line):
                if u'הקדמה' in line and u'פרק' not in line:
                    return True
                else:
                    return False
    def post_ab_index(self):
        if self.has_intro
            record = SchemaNode()
            record.add_title("Abarbanel on "+self.en_name, 'en', primary=True)
            record.add_title(u'אברבנאל על'+' '+self.he_name, 'he', primary=True)
            record.key = "Abarbanel on "+self.en_name
            
            intro_node = JaggedArrayNode()
            intro_node.add_title("Introduction", 'en', primary = True)
            intro_node.add_title("הקדמה", 'he', primary = True)
            intro_node.key = "Introduction"
            intro_node.depth = 1
            intro_node.addressTypes = ['Integer']
            intro_node.sectionNames = ['Paragraph']
            record.append(intro_node)
            
            text_node = JaggedArrayNode()
            text_node.key = "default"
            text_node.default = True
            text_node.depth = 3
            text_node.toc_zoom = 2
            text_node.addressTypes = ['Integer', 'Integer','Integer']
            text_node.sectionNames = ['Chapter','Verse','Comment']
            record.append(text_node)
        else:
            record = JaggedArrayNode()
            record.add_title("Abarbanel on "+self.en_name, 'en', primary=True)
            record.add_title(u'אברבנאל על'+' '+self.he_name, 'he', primary=True)
            record.key = "Abarbanel on "+self.en_name
            record.depth = 3
            record.toc_zoom = 2
            record.addressTypes = ["Integer", "Integer","Integer"]
            record.sectionNames = ["Chapter", "Verse", "Comment"]
    
        record.validate()
        
        cat = "Prophets" if self.en_name in prophet_list else "Writings"
        print "posting {} index..".format(self.en_name)
        index = {
            "title":"Abarbanel on "+self.en_name,
            "base_text_titles": [
              self.en_name
            ],
            "dependence": "Commentary",
            "collective_title":"Abarbanel",
            "categories":["Tanakh","Commentary","Abarbanel",cat],
            "schema": record.serialize()
        }
        post_index(index,weak_network=True)
    def post_ms_text(self, posting=True):
        with open(self.file_name) as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        text_array = make_perek_array(self.en_name)
        current_chapter=1
        current_verse=1
        for line in lines:
            if u'@' in line:
                current_chapter=getGematria(line)
            elif u'#' in line:
                current_verse=getGematria(line)
            elif not_blank(line):
                try:
                    text_array[current_chapter-1][current_verse-1].append(clean_line(line))
                except:
                    print "ERR",self.en_name
                    print line
                    0/0
        self.text=text_array
        version = {
            'versionTitle': "Arba'ah Ve'Esrim im Minhat Shai. Mantua, 1742-1744",
            'versionSource': 'http://primo.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH002093602&context=L',
            'language': 'he',
            'text': text_array
        }
        if posting:
            print "postinh {} text...".format(self.en_name)
            post_text_weak_connection("Abarbanel on "+self.en_name, version)
    def ms_link(self):
        self.post_ms_text(False)
        for perek_index,perek in enumerate(self.text):
            for pasuk_index, pasuk in enumerate(perek):
                for comment_index, comment in enumerate(pasuk):
                    link = (
                            {
                            "refs": [
                                     'Abarbanel on {}, {}:{}:{}'.format(self.en_name, perek_index+1, pasuk_index+1, comment_index+1),
                                     '{} {}:{}'.format(self.en_name,perek_index+1, pasuk_index+1),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_Minchat_Shai_linker"
                            })
                    post_link(link, weak_network=True)
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def clean_line(s):
    if s.count(u'.')+s.count(u':')>1:
        s =u'<b>'+s[:s.index(u'.')+1]+u'</b>'+s[s.index('.')+1:]
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
def add_cats():
    add_category('Abarbanel', ["Tanakh","Commentary","Abarbanel"],u'אברבנאל')
    add_category('Prophets', ["Tanakh","Commentary","Abarbanel","Prophets"],u'נביאים')
    add_category('Writings', ["Tanakh","Commentary","Abarbanel","Writings"],u'כתובים')

add_cats()
admin_links=[]
site_links=[]
for _file in os.listdir("files"):
    if 'txt' in _file:# and "איכ" not in _file:
        meg = megilah(_file)
        meg.post_ab_index()
        admin_links.append(SEFARIA_SERVER+"/admin/reset/Abarbanel on "+meg.en_name)
        site_links.append(SEFARIA_SERVER+"/Abarbanel on "+meg.en_name)
for link in admin_links:
    print link
print
for link in site_links:
    print link
        