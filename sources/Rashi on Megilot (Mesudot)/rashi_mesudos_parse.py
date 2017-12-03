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


title_dict = {'Esther':{"en_name":"Esther","he_name":u"אסתר"},
'Kohelet':{"en_name":"Ecclesiastes","he_name":u"קהלת"},
'Shir':{"en_name":"Song of Songs","he_name":u"שיר השירים"},
'Eicha':{"en_name":"Lamentations","he_name":u"איכה"},
'Ruth':{"en_name":"Ruth","he_name":u"רות"}}
class megilah:
    def __init__(self, file_name):
        self.file_name = file_name
        record_name=highest_fuzz(title_dict.keys(),file_name)
        self.megilah_name_he = title_dict[record_name]['he_name']
        self.megilah_name_en =title_dict[record_name]["en_name"]
        self.parse_text_mes()
    #final parsing methods:
    def parse_text_mes(self):
        with open("files/"+self.file_name) as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        en_text = make_perek_array(self.megilah_name_en)
        he_text = make_perek_array(self.megilah_name_en)
        current_pasuk = 0
        current_perek = 0
        for line in lines:
            if not_blank(line):
                if re.search(ur'\W\d+@',line):
                    match = re.search(ur'\W\d+@',line).group()
                    print match
                    current_pasuk=int(re.search(ur'\d+',match).group())
                if re.search(ur'CH\d+',line):
                    match=re.search(ur'CH\d+',line).group()
                    #print match
                    current_perek=int(re.search(ur'\d+',match).group())
                if re.search(ur'@p\d+',line):
                    #print line
                    en_text[current_perek-1][current_pasuk-1].append([u''])
                    he_text[current_perek-1][current_pasuk-1].append([u''])
                if u'<ENG>' in line:
                    en_text[current_perek-1][current_pasuk-1][-1]+=line
                elif u'<HEB>' in line:
                    he_text[current_perek-1][current_pasuk-1][-1]+=line
        self.en_text = make_perek_array(self.megilah_name_en)
        self.he_text = make_perek_array(self.megilah_name_en)
        for pindex, perek in enumerate(en_text):
            for paindex, pasuk in enumerate(perek):
                for comment in pasuk:
                    self.en_text[pindex][paindex].append(u''.join(comment))
                    
        for pindex, perek in enumerate(he_text):
            for paindex, pasuk in enumerate(perek):
                for cindex, commentw in enumerate(pasuk):
                    
                    self.he_text[pindex][paindex].append(fix_markers(''.join(commentw)))
        """
        for pindex, perek in enumerate(self.en_text):
            for paindex, pasuk in enumerate(perek):
                for cindex, comment in enumerate(pasuk):
                    print pindex, paindex, cindex, comment
        """
        for pindex, perek in enumerate(self.he_text):
            for paindex, pasuk in enumerate(perek):
                for cindex, comment in enumerate(pasuk):
                    print pindex, paindex, cindex, comment
    
                    
                    
        
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
    s= re.sub(ur'[\r\n<>A-Za-z@0-9]',u' ',s)
    s = re.sub(ur'\[.*?\]',u'',s)
    while u'  ' in s:
        s = s.replace(u'  ',u' ')
    s = u'<b>'+s
    s = s[:s.index(u'.')+1]+u'</b>'+s[s.index(u'.')+1:]
    return s

posting_text= False
linking=False
links=[]
reg_links=[]

for a_file in os.listdir("files"):
    if ".txt" in a_file and 'N' not in a_file:# and "נחו"  in a_file:
        
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
"""
example for comment eith footnotes:
<sup>1</sup><i class=\"footnote\">The Persians conquered the Babylonians, and Achashveirosh succeeded Koresh to the Persian throne in the year 3392.</i> who reigned in place of Koresh<sup>2</sup><i class=\"footnote\">There were other Persian kings with the name \u201cAchashveirosh,\u201d therefore Rashi identifies which \u201cAchashveirosh\u201d he was. (Mizrachi)</i>

key:
@pNUMBER=comment 
pasuk = (REGEX= \W\d@)
"""
#    22-23
#40