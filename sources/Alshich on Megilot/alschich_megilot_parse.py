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
from data_utilities.dibur_hamatchil_matcher import *


title_dict = {u"אסתר":{"en_name":"Esther","en_commentary_name":"Massat Moshe","he_commentary_name":u"משאת משה","chapter_mark":u"@00","skip":["@22"]},
u"קהלת":{"en_name":"Ecclesiastes","en_commentary_name":"Devarim Tovim","he_commentary_name":u"דברים טובים","chapter_mark":u"@00"},
u"שיר השירים":{"en_name":"Song of Songs","en_commentary_name":"Shoshanat haAmakim","he_commentary_name":u"שושנת העמקים","chapter_mark":u"@00"},
u"איכה":{"en_name":"Lamentations","en_commentary_name":"Devarim Nihumim","he_commentary_name":u"דברים נחומים","chapter_mark":u"@22"},
u"רות":{"en_name":"Ruth","en_commentary_name":"Ene Moshe","he_commentary_name":u"עיני משה","chapter_mark":"@00"}}
class megilah:
    def __init__(self, file_name):
        self.file_name = file_name
        self.megilah_name_he = highest_fuzz(title_dict.keys(),file_name.decode('utf8'))
        self.megilah_name_en =title_dict[self.megilah_name_he]["en_name"]
        self.he_commentary_name = title_dict[self.megilah_name_he]["he_commentary_name"]
        self.en_commentary_name = title_dict[self.megilah_name_he]["en_commentary_name"]
        self.chapter_mark=title_dict[self.megilah_name_he]["chapter_mark"]
        self.initial_parse_text()
    #we need to make "initial" texts for matching...
    def initial_post_term(self):
        #for posting commentary term for first time
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
    def initial_index_post(self):
        record = JaggedArrayNode()
        record.add_title(self.en_commentary_name+' on '+self.megilah_name_en, 'en', primary=True)
        record.add_title(self.he_commentary_name+u' על'+' '+self.megilah_name_he, 'he', primary=True)
        record.key = self.en_commentary_name+' on '+self.megilah_name_en
        record.depth = 2
        record.addressTypes = ["Integer", "Integer"]
        record.sectionNames = ["Chapter", "Comment"]
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
    def initial_parse_text(self):
        with open("texts/"+self.file_name) as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        past_start = False
        perek_box = []
        perek_list = []
        for line in lines:
            if u"פרק א" in line:
                past_start=True
            elif past_start:
                if self.chapter_mark in line:
                    perek_list.append(perek_box)
                    perek_box=[]
                elif "@11" in line:
                    perek_box.append(line)
        perek_list.append(perek_box)
        self.text = perek_list
        
    def initial_post_text(self):
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': self.text
        }
        post_text_weak_connection(self.en_commentary_name+' on '+self.megilah_name_en, version)
    def initial_link_text(self):
        f = open(megilah_object.en_commentary_name+" Engineer Links.txt","a")
        for chapter_index in range(1,len(TextChunk(Ref(self.en_commentary_name+' on '+self.megilah_name_en),"he").text)+1):
            alshich_chunk=TextChunk(Ref(self.en_commentary_name+' on '+self.megilah_name_en+' '+str(chapter_index)),"he")
            base_chunk = TextChunk(Ref(self.megilah_name_en+' '+str(chapter_index)),"he",'Tanach with Text Only')
            alshich_links = match_ref(base_chunk,alshich_chunk,base_tokenizer,dh_extract_method=dh_extract_method,verbose=True,rashi_filter=a_filter)
            if "comment_refs" in alshich_links:
                for base, comment in zip(alshich_links["matches"],alshich_links["comment_refs"]):
                        print "B",base,"C", comment
                        if base:
                            f.write("BASE: "+base.normal()+"\n")
                        else:
                            f.write("NO BASE MATCH:"+"\n")
                        f.write("ALSHICH LOCATION: "+comment.normal()+"\n")
                         
                        f.write(TextChunk(comment,"he").text.encode('utf8')+"\n")
                        """
                        print link.get('refs')
                        if base:
                            link = (
                                    {
                                    "refs": [
                                             base.normal(),
                                             comment.normal(),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_avi_ezer_alshich_linker"
                                    })
                            post_link(link, weak_network=True)  
                        """
            else:
                f.write("NO MATCHES AT ALL IN "+self.en_commentary_name+' on '+self.megilah_name_en+' '+str(chapter_index))
        f.close()
        
def a_filter(some_string):
    if re.search(ur'@11(.*?)@33', some_string) is None:
        return False
    else:
        return True

def dh_extract_method(some_string):
    return re.search(ur'@11(.*?)@33', some_string.replace("\n","")).group(1)

def base_tokenizer(some_string):
    return some_string.replace(u"<b>",u"").replace(u"</b>",u"").replace(".","").split(" ")

def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match
def not_blank(s):
    while u" " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
posting_term=False
posting_index = False
posting_text=False
linking=True
links=[]
for a_file in os.listdir("texts"):
    if ".txt" in a_file and "סתרים" not in a_file:
        megilah_object = megilah(a_file)
        f = open(megilah_object.en_commentary_name+" Engineer Links.txt","w")
        f.close()
        if posting_term:
            megilah_object.initial_post_term()
        if posting_index:
            megilah_object.initial_index_post()
        if posting_text:
            megilah_object.initial_post_text()
        if linking:
            megilah_object.initial_link_text()
        links.append("localhost:8000/admin/reset/"+megilah_object.en_commentary_name+' on '+megilah_object.megilah_name_en)
for link in links:
    print link
