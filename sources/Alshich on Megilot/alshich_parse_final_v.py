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
        self.final_parse_text()
    #final parsing methods:
    def final_parse_text(self):
        with open("marked_texts/"+self.file_name) as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        past_start = False
        self.comm_intro = []
        self.text = make_perek_array(self.megilah_name_en)
        current_pasuk = 0
        current_perek = 0
        for line in lines:
            if not_blank(line):
                if u"פרק א" in line and not past_start:
                    past_start=True
                    current_perek=1
                elif u"@00" not in line and not past_start:
                    self.comm_intro.append(fix_markers(line))
                elif past_start:
                    if u"@00" in line:
                        current_perek=getGematria(line.replace(u"פרק",u""))
                    elif "@22" in line:
                        current_pasuk=getGematria(line)
                    else:
                        self.text[current_perek-1][current_pasuk-1].append(fix_markers(line))
        
    def final_index_post(self):
        if len(self.comm_intro)>0:
            record = SchemaNode()
            record.add_title('Alshich on '+self.megilah_name_en, 'en', primary=True)
            record.add_title(u'אלשיך'+u' על'+' '+self.megilah_name_he, 'he', primary=True)
            record.key = "Alshich"+' on '+self.megilah_name_en
            intro_node = JaggedArrayNode()
            intro_node.add_title("Introduction", 'en', primary = True)
            intro_node.add_title(u"הקדמה", 'he', primary = True)
            intro_node.key = "Introduction"
            intro_node.depth = 1
            intro_node.addressTypes = ['Integer']
            intro_node.sectionNames = ['Paragraph']
            record.append(intro_node)

            text_node = JaggedArrayNode()
            text_node.key = "default"
            text_node.default = True
            text_node.depth = 3
            text_node.addressTypes = ['Integer','Integer','Integer']
            text_node.sectionNames = ['Chapter','Verse','Comment']
            text_node.toc_zoom = 2
            
            record.append(text_node)
        else:
            record = JaggedArrayNode()
            record.add_title("Alshich"+' on '+self.megilah_name_en, 'en', primary=True)
            record.add_title(u"אלשיך"+u' על'+' '+self.megilah_name_he, 'he', primary=True)
            record.key = "Alshich"+' on '+self.megilah_name_en
            record.depth = 3
            record.toc_zoom = 2
            record.addressTypes = ["Integer", "Integer","Integer"]
            record.sectionNames = ["Chapter", "Verse", "Comment"]
        
        record.validate()

        index = {
            "title":"Alshich"+' on '+self.megilah_name_en,
            "titleVariants": [self.en_commentary_name, self.he_commentary_name],
            "base_text_titles": [
              self.megilah_name_en
            ],
            "dependence": "Commentary",
            "collective_title":"Alshich",
            "categories":["Tanakh","Commentary","Alshich",get_book_category(self.megilah_name_en)],
            "schema": record.serialize()
        }
        post_index(index,weak_network=True)
    def final_post_text(self):
        if len(self.comm_intro)>0:
            version = {
                'versionTitle': 'Alshich on Five Megillot, Warsaw, 1862',
                'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001268473',
                'language': 'he',
                'text': self.comm_intro
            }
            post_text_weak_connection("Alshich"+' on '+self.megilah_name_en+", Introduction", version)
        version = {
            'versionTitle': 'Alshich on Five Megillot, Warsaw, 1862',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001268473',
            'language': 'he',
            'text': self.text
        }
        post_text_weak_connection("Alshich"+' on '+self.megilah_name_en, version)
    def final_link_text(self):
        for perek_index,perek in enumerate(self.text):
            for pasuk_index, pasuk in enumerate(perek):
                has_bold_in_pasuk=False
                for comment_index, comment in enumerate(pasuk):
                    if u"<b>" in comment:
                        range_length = 0
                        has_bold_in_pasuk = True
                        hit_bold=False
                        while comment_index+range_length+1<len(pasuk) and not hit_bold:
                            if u"<b>" not in pasuk[comment_index+range_length+1]:
                                range_length+=1
                            else:
                                hit_bold=True
                        print '{} on {}, {}:{}:{}-{}'.format("Alshich",self.megilah_name_en, perek_index+1, pasuk_index+1, comment_index+1, comment_index+range_length+1)

                        link = (
                                {
                                "refs": [
                                         '{} on {}, {}:{}:{}-{}'.format("Alshich",self.megilah_name_en, perek_index+1, pasuk_index+1, comment_index+1, comment_index+range_length+1),
                                         '{} {}:{}'.format(self.megilah_name_en,perek_index+1, pasuk_index+1),
                                         ],
                                "type": "commentary",
                                "auto": True,
                                "generated_by": "sterling_"+self.megilah_name_en+"_linker"
                                })
                        post_link(link, weak_network=True)
                    elif not has_bold_in_pasuk:
                        link = (
                                {
                                "refs": [
                                         '{} on {}, {}:{}:{}'.format("Alshich",self.megilah_name_en, perek_index+1, pasuk_index+1, comment_index+1),
                                         '{} {}:{}'.format(self.megilah_name_en,perek_index+1, pasuk_index+1),
                                         ],
                                "type": "commentary",
                                "auto": True,
                                "generated_by": "sterling_"+self.megilah_name_en+"_linker"
                                })
                        post_link(link, weak_network=True)
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
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match
def get_book_category(book):
    if type(book)==str:
        book = book.decode('utf8')
    categories = ["Torah","Prophets","Writings"]
    for cat in categories:
        if book in library.get_indexes_in_category(cat):
            return cat
    return None
def not_blank(s):
    while u" " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def fix_markers(s):
    return s.replace(u"@44",u"").replace(u"@99",u"").replace(u"@11",u"<b>").replace(u"@33",u"</b>").replace(u"@44",u"<b>").replace(u"@55",u"</b>")
def al_post_term():
    #for posting commentary term for first time
    term_obj = {
        "name": "Alshich",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Alshich",
                "primary": True
            },
            {
                "lang": "he",
                "text": u"אלשיך",
                "primary": True
            }
        ]
    }
    post_term(term_obj)
def post_al_categories():
    add_category('Alshich', u'אלשיך', ["Tanakh","Commentary","Alshich"])
    add_category('Writings', u'כתובים', ["Tanakh","Commentary","Alshich",'Writings'])
posting_term=True
posting_cat = True
posting_index = True
posting_text= True
linking=True
links=[]
reg_links=[]

if posting_term:
    al_post_term()
if posting_cat:
    post_al_categories()
for a_file in os.listdir("marked_texts"):
    if ".txt" in a_file:# and "נחו"  in a_file:
        
        megilah_object = megilah(a_file)
        """
        for cindex, chapter in enumerate(megilah_object.text):
            for pindex, pasuk in enumerate(chapter):
                for coindex, comment in enumerate(pasuk):
                    print megilah_object.megilah_name_en,cindex, pindex, coindex, comment
        """

        if posting_index:
            megilah_object.final_index_post()
        if posting_text:
            megilah_object.final_post_text()
        if linking:
            megilah_object.final_link_text()
        links.append(SEFARIA_SERVER+"/admin/reset/"+'Alshich on '+megilah_object.megilah_name_en)
        reg_links.append(SEFARIA_SERVER+"/"+'Alshich on '+megilah_object.megilah_name_en)
for link in links:
    print link
for link in reg_links:
    print link
