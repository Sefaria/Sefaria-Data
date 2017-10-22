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

title_dict = {u"אמרי יושר":{"english_book_name":"Ruth","hebrew_book_name":u"רות","english_comment_name":"Imrei Yosher"},
u"מגילת סתרים":{"english_book_name":"Esther","hebrew_book_name":u"אסתר","english_comment_name":"Megillat Setarim"},
u"פלגי מים":{"english_book_name":"Lamentations","hebrew_book_name":u"איכה","english_comment_name":"Palgei Mayim"},
u"צרור המור":{"english_book_name":"Song of Songs","hebrew_book_name":u"שיר השירים","english_comment_name":"Tzror HaMor"},
u"תעלומות חכמה":{"english_book_name":"Ecclesiastes","hebrew_book_name":u"קהלת","english_comment_name":"Ta'alumot Chokmah"}}
class megilah:
    def __init__(self, file_name):
        self.file_name = file_name
        self.he_commentary_name = highest_fuzz(title_dict.keys(),file_name.decode('utf8'))
        self.en_commentary_name = title_dict[self.he_commentary_name]["english_comment_name"]
        self.megilah_name_en =title_dict[self.he_commentary_name]["english_book_name"]
        self.megilah_name_he = title_dict[self.he_commentary_name]["hebrew_book_name"]
        self.parse_text()
    def n_post_term(self):
        term_obj = {
            "name": self.en_commentary_name,
            "scheme": "commentary_works",
            "titles": [
                {
                    "lang": "en",
                    "text": self.en_commentary_name,
                    "primary": True
                },
                {
                    "lang": "he",
                    "text": self.he_commentary_name,
                    "primary": True
                }
            ]
        }
        post_term(term_obj)
    def parse_text(self):
        with open("files/"+self.file_name) as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        self.text = make_perek_array(self.megilah_name_en)
        past_start = False
        in_intro = False
        in_forward=False
        self.forward = []
        self.introduction=[]
        current_chapter=0
        current_verse=0
        for line in lines:
            if u"START" in line:
                past_start=True
            elif past_start:
                if u"@00" in line:
                    current_chapter=getGematria(line.replace(u"פרק",""))
                    #print "CHAPTER: ", line, self.megilah_name_en
                elif "@22" in line:
                    #print "VERSE: ",line
                    current_verse=getGematria(line)
                else:
                    self.text[current_chapter-1][current_verse-1].append(fix_markers(line))
            elif u"@00הקדמת" in line:
                in_intro=True
            elif in_intro:
                self.introduction.append(line)
            elif u"@00פתיחה" in line:
                in_forward=True
            elif in_forward:
                self.forward.append(line)
    def n_post_index(self):
        if len(self.introduction)>0:
            record = SchemaNode()
            record.add_title(self.en_commentary_name+' on '+self.megilah_name_en, 'en', primary=True)
            record.add_title(self.he_commentary_name+u' על'+' '+self.megilah_name_he, 'he', primary=True)
            record.key = self.en_commentary_name+' on '+self.megilah_name_en
            if len(self.introduction)>0:
                intro_node = JaggedArrayNode()
                intro_node.add_title("Introduction", 'en', primary = True)
                intro_node.add_title("הקדמת", 'he', primary = True)
                intro_node.key = "Introduction"
                intro_node.depth = 1
                intro_node.addressTypes = ['Integer']
                intro_node.sectionNames = ['Paragraph']
                record.append(intro_node)
            if len(self.forward)>0:
                forward_node = JaggedArrayNode()
                forward_node.add_title("Forward", 'en', primary = True)
                forward_node.add_title(u"פתיחה", 'he', primary = True)
                forward_node.key = "Forward"
                forward_node.depth = 1
                forward_node.addressTypes = ['Integer']
                forward_node.sectionNames = ['Paragraph']
                record.append(forward_node)
            text_node = JaggedArrayNode()
            text_node.key = "default"
            text_node.default = True
            text_node.depth = 3
            text_node.addressTypes = ['Integer', 'Integer','Integer']
            text_node.sectionNames = ['Chapter','Verse','Comment']
            record.append(text_node)
        else:
            record = JaggedArrayNode()
            record.add_title(self.en_commentary_name+' on '+self.megilah_name_en, 'en', primary=True)
            record.add_title(self.he_commentary_name+u' על'+' '+self.megilah_name_he, 'he', primary=True)
            record.key = self.en_commentary_name+' on '+self.megilah_name_en
            record.depth = 3
            record.addressTypes = ["Integer", "Integer","Integer"]
            record.sectionNames = ["Chapter", "Verse", "Comment"]
        
        record.validate()

        index = {
            "title":self.en_commentary_name+' on '+self.megilah_name_en,
            "base_text_titles": [
              self.megilah_name_en
            ],
            "dependence": "Commentary",
            "collective_title":self.en_commentary_name,
            "categories":["Tanakh",self.megilah_name_en,"Commentary",self.en_commentary_name],
            "schema": record.serialize()
        }
        post_index(index,weak_network=True)
    def n_post_text(self):
        if len(self.introduction)>0:
            version = {
                'versionTitle': 'Alshich on Five Megillot, Warsaw, 1862',
                'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001268473',
                'language': 'he',
                'text': self.introduction
            }
            post_text_weak_connection(self.en_commentary_name+' on '+self.megilah_name_en+", Introduction", version)
        if len(self.forward)>0:
            version = {
                'versionTitle': 'Alshich on Five Megillot, Warsaw, 1862',
                'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001268473',
                'language': 'he',
                'text': self.forward
            }
            post_text_weak_connection(self.en_commentary_name+' on '+self.megilah_name_en+", Forward", version)
        version = {
            'versionTitle': 'Alshich on Five Megillot, Warsaw, 1862',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001268473',
            'language': 'he',
            'text': self.text
        }
        post_text_weak_connection(self.en_commentary_name+' on '+self.megilah_name_en, version)
    def n_link(self):
        for perek_index,perek in enumerate(self.text):
            for pasuk_index, pasuk in enumerate(perek):
                for comment_index, comment in enumerate(pasuk):
                    link = (
                            {
                            "refs": [
                                     '{} on {}, {}:{}:{}'.format(self.en_commentary_name,self.megilah_name_en, perek_index+1, pasuk_index+1, comment_index+1),
                                     '{} {}:{}'.format(self.megilah_name_en,perek_index+1, pasuk_index+1),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_"+self.megilah_name_en+"_linker"
                            })
                    post_link(link, weak_network=True)
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match
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
def fix_markers(s):
    return s.replace(u"@11",u"<b>").replace(u"@33",u"</b>")
admin_links = []
site_links = []
posting_term=True
posting_index = True
posting_text = True
linking = True
for n_file in os.listdir("files"):
    if ".txt" in n_file and "אמרי" not in n_file and "צרור" not in n_file:
        current_megilah = megilah(n_file)
        admin_links.append(SEFARIA_SERVER+"/admin/reset/"+current_megilah.en_commentary_name.replace(u" ",u"_"))
        site_links.append(SEFARIA_SERVER+"/"+current_megilah.en_commentary_name.replace(u" ",u"_"))
        if posting_term:
            print "posting ",current_megilah.megilah_name_en," term..."
            current_megilah.n_post_term()
        if posting_index:
            print "posting ",current_megilah.megilah_name_en," index..."
            current_megilah.n_post_index()
        if posting_text:
            print "posting ",current_megilah.megilah_name_en," text..."
            current_megilah.n_post_text()
        if linking:
            print "linking",current_megilah.megilah_name_en,"..."
            current_megilah.n_link()
        
print "Admin Links:"
for link in admin_links:
    print link
print "Site Links:"
for link in site_links:
    print link
