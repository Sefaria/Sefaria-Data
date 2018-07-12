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
                    #print match
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
        self.comment_array = self.get_comment_array()
        for pindex, perek in enumerate(en_text):
            for paindex, pasuk in enumerate(perek):
                for comment_list in pasuk:
                    comment=u''.join(comment_list)
                    for footnote_marker in re.findall(ur'<\$\d+ \d+>\d*',comment):
                        footnote_number = int(re.search(ur'\d+(?=>)',footnote_marker).group())
                        comment = comment.replace(footnote_marker, u'<sup>'+str(footnote_number)+'</sup><i class=\"footnote\">'+self.comment_array[pindex].pop(0)+'</i>')
                    self.en_text[pindex][paindex].append(fix_markers_en(comment))
        
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
        """
        for pindex, perek in enumerate(self.he_text):
            for paindex, pasuk in enumerate(perek):
                for cindex, comment in enumerate(pasuk):
                    print pindex, paindex, cindex, comment
    
        """           
                    
        
    def post_text_mes(self):
        version = {
            'versionTitle': 'The Metsudah Five Megillot, Lakewood, N.J., 2001',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002162036',
            'language': 'he',
            'text': self.he_text
        }
        post_text_weak_connection("Rashi"+' on '+self.megilah_name_en, version)
        
        version = {
            'versionTitle': 'The Metsudah Five Megillot, Lakewood, N.J., 2001',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002162036',
            'language': 'en',
            'text': self.en_text
        }
        post_text_weak_connection("Rashi"+' on '+self.megilah_name_en, version)
    def get_comment_array(self):
        #comments continue through chapter, so we return a list of comments for each chapter.
        with open("files/"+self.file_name.replace('Rashi','N_')) as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        return_array = []
        for x in range(len(TextChunk(Ref(self.megilah_name_en), "he").text)):
            return_array.append([])
        current_perek = 0
        for line in lines:
            if re.search(ur'CH\d+',line):
                match=re.search(ur'CH\d+',line).group()
                current_perek=int(re.search(ur'\d+',match).group())
            list_of_comments= line.split(u"<$")
            for comment in list_of_comments:
                if not_blank(comment) and u'CH' not in comment:
                    return_array[current_perek-1].append(fix_comment_markers(comment))
        """
        for pindex, perek in enumerate(return_array):
            for cindex, comment in enumerate(perek):
                print self.megilah_name_en, "COMMENT",pindex, cindex, comment
        """
        return return_array
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
def not_blank(s):
    while u" " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def fix_markers(s):
    s= re.sub(ur'[\r\n<>A-Za-z@0-9]',u' ',s)
    s = re.sub(ur'\[.*?\]',u'',s)
    s = s.replace(u'§',u'ךָ')
    while u'  ' in s:
        s = s.replace(u'  ',u' ')
    if u'.' in s:
        s = u'<b>'+s
        s = s[:s.index(u'.')+1]+u'</b>'+s[s.index(u'.')+1:]
    return s
def fix_markers_en(s):
    s= re.sub(ur'[\r\n]',u' ',s)
    s = re.sub(ur'@[\dA-Za-z]*',u'',s)
    s = re.sub(ur'\[.*?CH\d.*?\]',u'',s)
    s = re.sub(ur'\[\d+\]',u'',s)
    s = s.replace(u'<ENG>]',u'').replace(u'[<HEB>',u'')
    s = s.replace(u'.<TIE>.<TIE>.<TIE>',u'…')
    substrings_to_remove = [u'<ENG>',u'<HEB>',u'<EM>',u'<TIE>',u'<tie>']
    s = remove_substrings(s, substrings_to_remove)
    s = s.replace(u'_',u'-').replace(u'±',u'-').replace(u'׀',u'—')
    while u'  ' in s:
        s = s.replace(u'  ',u' ')
    if u'.' in s:
        s = u'<b>'+s
        s = s[:s.index(u'.')+1]+u'</b>'+s[s.index(u'.')+1:]
    return s
def remove_substrings(s, substring_list):
    for substring in substring_list:
        s = s.replace(substring, u'')
    return s
def fix_comment_markers(s):
    s = re.sub(ur'[\d><]+TS>',u'',s)
    s = re.sub(ur'<.*?>',u'',s)
    s = s.replace(u'@ms',u'').replace(u'@hh',u'').replace(u'@ee',u'')
    while u'_  ' in s:
        s = s.replace(u'_  ',u'_ ')
    s = s.replace(u'_ ',u'')
    s.replace(u'_',u'-')
    s = re.sub(ur'^\s*1\s*',u'',s)
    return s

posting_text= True
links=[]
reg_links=[]

for a_file in os.listdir("files"):
    if ".txt" in a_file and 'N' not in a_file and 'Esther' not in a_file:# and "נחו"  in a_file:
        
        megilah_object = megilah(a_file)
        if posting_text:
            print 'posting '+megilah_object.megilah_name_en+' text...'
            megilah_object.post_text_mes()
        links.append(SEFARIA_SERVER+"/admin/reset/"+'Rashi on '+megilah_object.megilah_name_en)
        reg_links.append(SEFARIA_SERVER+"/"+'Rashi on '+megilah_object.megilah_name_en)
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