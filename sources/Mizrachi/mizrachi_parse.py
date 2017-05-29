# -*- coding: utf-8 -*-
import sys
import os
import num2words
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
from sefaria.model.text import *
import re
import codecs
from data_utilities.dibur_hamatchil_matcher import *
import pdb


class Book:
    def __init__(self,file_name):
        self.file_name = file_name
        self.en_name = file_name.replace("Mizrachi ","").replace(".txt","").decode('utf-8')
        self.he_name = Ref(self.en_name).he_normal()
        self.text = self._parse_text()
    def _parse_text(self):
        with open("files/"+self.file_name) as myfile:
            lines = list(map(lambda x: x.decode("utf-8",'replace'), myfile.readlines()))
        perek_list = make_perek_array(self.en_name)
        past_start = False
        current_perek = 1
        current_pasuk = 1
        for line in lines:
            if u"@00" in  line:
                current_perek=getGematria(line)
                past_start=True
            elif u"@22" in line:
                current_pasuk=getGematria(line)
            elif past_start and not_blank(line) and u"@88" not in line and u"@99" not in line:
                perek_list[current_perek-1][current_pasuk-1].append(fix_line(line))
        return perek_list 
    
    def m_post_text(self):
        version = {
            'versionTitle': 'Four commentaries on Rashi. Warsaw, 1862, '+self.en_name,
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001276251',
            'language': 'he',
            'text': self.text
        }
        if "local" in SEFARIA_SERVER:
            post_text('Mizrachi, '+self.en_name, version,skip_links=True, index_count="on")
        else:
            post_text('Mizrachi, '+self.en_name, version, weak_network=True)
            
    def m_make_links(self):
        matched=0.00
        total=0.00
        errored = []
        not_machted = []
        sample_Ref = Ref("Genesis 1")
        for perek_index,perek in enumerate(self.text):
            for pasuk_index, pasuk in enumerate(perek):
                for comment_index, comment in enumerate(pasuk):
                    #link to Torah and Rashi
                    link = (
                            {
                            "refs": [
                                     'Mizrachi, {}, {}:{}:{}'.format(self.en_name, perek_index+1, pasuk_index+1, comment_index+1),
                                     '{} {}:{}'.format(self.en_name,perek_index+1, pasuk_index+1),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_mizrachi_torah_linker"
                            })
                    post_link(link, weak_network=True)
                    try:
                        base_ref = TextChunk(Ref('Rashi on {}, {}:{}'.format(self.en_name,perek_index+1, pasuk_index+1)),"he")
                        mizrachi_ref = TextChunk(Ref('Mizrachi, {}, {}:{}:{}'.format(self.en_name, perek_index+1, pasuk_index+1, comment_index+1)),"he")
                        mizrachi_links = match_ref(base_ref,mizrachi_ref,base_tokenizer,dh_extract_method=dh_extract_method,verbose=False)
                    except IndexError:
                        errored.append('Mizrachi on {}, {}:{}'.format(self.en_name,perek_index+1, pasuk_index+1))
                    for base, comment in zip(mizrachi_links["matches"],mizrachi_links["comment_refs"]):
                        print "B",base,"C", comment
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
                                    "generated_by": "sterling_mizrachi_rashi_linker"
                                    })
                            post_link(link, weak_network=True)    
                            matched+=1
                        #if there is no match and there is only one comment, default will be to link it to that comment    
                        elif len(base_ref.text)==1:
                            link = (
                                    {
                                    "refs": [
                                             'Rashi on {}, {}:{}:1'.format(self.en_name,perek_index+1, pasuk_index+1),
                                             'Mizrachi, {}, {}:{}:{}'.format(self.en_name, perek_index+1, pasuk_index+1, comment_index+1),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_mizrachi_rashi_linker"
                                    })
                            post_link(link, weak_network=True)    
                            matched+=1
                        else:
                            not_machted.append('Mizrachi, {}, {}:{}:{}'.format(self.en_name, perek_index+1, pasuk_index+1, comment_index+1))
                        total+=1
        pm = matched/total
        print self.en_name
        print "Result is:",matched,total
        print "Percent matched: "+str(pm)
        print "Not Matched:"
        for nm in not_machted:
            print nm
        print "Errored:"
        for error in errored:
            print error
def fix_line(s):
    return remove_extra_space(s.replace(u"@11",u"<b>").replace(u"@33",u"</b>").replace(u"T",u""))
def remove_extra_space(string):
    while u"  " in string:
        string = string.replace(u"  ",u" ")
    return string
    
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
def not_blank(s):
    while u" " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
    

#here starts methods for linking:
def _filter(some_string):
    if re.search(ur'<b>(.*?)</b>', some_string) is None:
        return False
    else:
        return True

def dh_extract_method(some_string):
    """
    split_group = some_string.split(u"וכו"+u"'")
    if u"וגומר" in some_string:
        split_group=some_string.split(u"וגומר")
    if len(split_group[0])>5:
        some_string=split_group[0]+u"</b>"
    """
    print some_string
    return re.search(ur'<b>(.*?)</b>', some_string.replace("\n","")).group(1)

def base_tokenizer(some_string):
    return some_string.replace(u"<b>",u"").replace(u"</b>",u"").replace(".","").split(" ")
def m_post_index():
    # create index record
    record = SchemaNode()
    record.add_title('Mizrachi', 'en', primary=True, )
    record.add_title(u'מזרכי', 'he', primary=True, )
    record.key = 'Mizrachi'

    en_sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
    he_sefer_names =  [u"בראשית",u"שמות" ,u"ויקרא",u"במדבר",u"דברים"]
    for en_sefer, he_sefer in zip(en_sefer_names, he_sefer_names):
        sefer_node = JaggedArrayNode()
        sefer_node.add_title(en_sefer, 'en', primary=True, )
        sefer_node.add_title(he_sefer, 'he', primary=True, )
        sefer_node.key = en_sefer
        sefer_node.depth = 3
        sefer_node.toc_zoom = 2
        sefer_node.addressTypes = ['Integer', 'Integer','Integer']
        sefer_node.sectionNames = ['Chapter','Verse','Comment']
        record.append(sefer_node)

    record.validate()

    index = {
        "title":"Mizrachi",
        "base_text_titles": [
           "Genesis","Exodus","Leviticus","Numbers","Deuteronomy"
        ],
        "dependence": "Commentary",
        "categories":['Tanakh','Commentary','Mizrachi','Torah'],
        "schema": record.serialize(),
        "collective_title":"Mizrachi",
    
    }
    post_index(index,weak_network=True)
def m_post_term():
    term_obj = {
        "name": "Mizrachi",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Mizrachi",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'מזרכי',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
posting_term=False
posting_index = False
posting_text=True
posting_links=True
if posting_term:
    m_post_term()
if posting_index:
    m_post_index()
for m_file in os.listdir("files"):
    if ".txt" in m_file and "Deu" not in m_file:
        book = Book(m_file)
        if posting_text:
            print "posting ",book.en_name," text..."
            book.m_post_text()
        if posting_links:
            print "posting ",book.en_name," links..."
            book.m_make_links()
            
 