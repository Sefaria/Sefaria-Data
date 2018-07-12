# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
import re
import codecs
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from data_utilities.dibur_hamatchil_matcher import *
import pdb

tractate_titles = {}
for tractate_title in library.get_indexes_in_category("Bavli"):
    he_title = library.get_index(tractate_title).get_title("he")
    tractate_titles[he_title]=tractate_title
    
class RNG_Tractate:
    def __init__(self, file_name):
            self.file_name = file_name
            self.he_tractate_name = get_hebrew_name(' '.join(file_name.split()[2:-1]).decode('utf8'))
            self.en_tractate_name = tractate_titles[self.he_tractate_name]
            self.parse_tractate()
            print self.he_tractate_name
    def make_tractate_index(self):
        en_title = self.en_tractate_name
        he_title = self.he_tractate_name
        record = JaggedArrayNode()
        record.add_title('Rav Nissim Goan on '+en_title, 'en', primary=True)
        record.add_title(u"רב נסים גאון על מסכת"+u" "+he_title, 'he', primary=True)
        record.key = 'Rav Nissim Goan on '+en_title
        record.depth = 2
        record.addressTypes = ['Talmud', 'Integer']
        record.sectionNames = ['Daf','Comment']
        record.validate()

        index = {
            "title":'Rav Nissim Goan on '+en_title,
            "base_text_titles": [
               en_title
            ],
            "collective_title":"Rav Nissim Goan",
            "dependence": "Commentary",
            "categories":["Talmud","Bavli","Commentary","Rav Nissim Goan"],
            "schema": record.serialize()
        }
        post_index(index,weak_network=True)
        
    def parse_tractate(self):
        print self.en_tractate_name
        with open("files/"+self.file_name) as myFile:
            lines = list(map(lambda x: x.decode("utf8",'replace'), myFile.readlines()))
        mesechet_array = make_talmud_array(self.en_tractate_name)
        past_start=False
        #dict contains daf and amud
        current_daf_ref = {}
        #subtract 2 since we start at 0, add one since range's range is non-inclusive
        final_list = [[] for x in range(len(TextChunk(Ref(self.en_tractate_name),"he").text)-1)]
        for line in lines:
            if u"IGNORE" not in line:
                if u"@" in line and u"=" not in line:
                    current_daf_ref = extract_daf(line)
                    past_start=True
                elif past_start:
                    if not_blank(line):
                        final_list[get_page(current_daf_ref["daf"],current_daf_ref["amud"])].append(remove_markers(line).strip())

        #add blank to offset beggening:
        #box for adding to amud what is removed during transfer
        add_after = []
        final_list.insert(0,[])
        
        for previous_amud_index, amud in enumerate(final_list[1:]):
            if len(amud)>0 and len(final_list[previous_amud_index])>0 and len(final_list[previous_amud_index][-1])>0:
                if final_list[previous_amud_index][-1][-1]!=u"." and final_list[previous_amud_index][-1][-1]!=u":":
                    amud_split = re.findall(ur".*?[\.:]",amud[0])
                    previous_amud_dangler = re.split(ur"[\.:]",final_list[previous_amud_index][-1])[-1]
                    if len(amud_split)>0:
                        if len(previous_amud_dangler)>len(amud_split[0]):
                            print previous_amud_index
                            print "Pulled Back!"
                            if amud[0][-1]!=u"." and amud[0][-1]!=u":":
                                add_after.append(re.split(ur"[\.:]",amud[0])[-1])
                            print amud_split[0]
                            final_list[previous_amud_index][-1]+=u" "+amud_split[0]
                            final_list[previous_amud_index+1][0]=None if len(amud_split)<1 else ''.join(amud_split[1:])
                            while len(add_after)>0:
                                final_list[previous_amud_index+1][0]+=add_after.pop()
                        else:
                            print previous_amud_index
                            print "Pushed Forward!"
                            final_list[previous_amud_index][-1]=''.join(re.findall(ur".*?[\.|:]",final_list[previous_amud_index][-1]))
                            final_list[previous_amud_index+1][0]=previous_amud_dangler+u" "+final_list[previous_amud_index+1][0]
        for dindex, daf in enumerate(final_list):
            for cindex, comment in enumerate(daf):
                print dindex, cindex, comment
        self.text = final_list
    
    def rc_post_text(self):
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': ' http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'text': self.text,
            'language': 'he'
            
        }
        post_text('Rav Nissim Goan on '+self.en_tractate_name, version,weak_network=True)# skip_links=True, index_count="on")
    def rc_link(self):
        for amud_index in range(1,len(TextChunk(Ref(self.en_tractate_name)).text)-1):
            if amud_index>0:
                #not every amud has a comment...
                try:
                    rng_ref=Ref('Rav Nissim Goan on '+self.en_tractate_name+"."+get_daf_en(amud_index))
                    rng_chunk = TextChunk(rng_ref,"he")
                except:
                    print "No RC on Rav Nissim Goan on ",self.en_tractate_name,".",get_daf_en(amud_index)
                    continue
                #for Rav Channanel, each "comment" contains comments on several passages.
                #therefore, link each comment to the whole amud
                print get_daf_en(amud_index)
                tractate_ref=Ref(self.en_tractate_name+"."+get_daf_en(amud_index))
                tractate_chunk = TextChunk(tractate_ref,"he")
                matches = match_ref(tractate_chunk,rng_chunk,base_tokenizer,dh_extract_method=dh_extract_method,verbose=True)
                if "comment_refs" in matches:
                    for link_index, (base, comment) in enumerate(zip(matches["matches"],matches["comment_refs"])):
                        if base:
                            if "-" in base.normal():
                                base=Ref(base.normal().split("-")[0])
                                print "I just changed"
                            print "MATCHED BC:",base,comment,base.normal()+"-"+tractate_ref.as_ranged_segment_ref().normal().split("-")[-1]
                            link = (
                                    {
                                    "refs": [
                                             base.normal()+"-"+tractate_ref.as_ranged_segment_ref().normal().split("-")[-1],
                                             comment.normal(),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_tos_rid_linker"
                                    })
                            post_link(link, weak_network=True)
                            
                        else:
                            print "UNMATCHED REF: ",comment
                            link = (
                                    {
                                    "refs": [
                                             tractate_ref.as_ranged_segment_ref().normal(),
                                             comment.normal(),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_Rav_Nissim_Goan_"+self.en_tractate_name+"_linker"
                                    })
                            post_link(link, weak_network=True)
                else:
                    print "UNMATCHED REF: ",rng_ref
                    link = (
                            {
                            "refs": [
                                     tractate_ref.as_ranged_segment_ref().normal(),
                                     rng_ref.normal(),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_Rav_Nissim_Goan_"+self.en_tractate_name+"_linker"
                            })
                    post_link(link, weak_network=True)
def make_talmud_array(book):
    tc = TextChunk(Ref(book), "he")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    for index, perek in enumerate(return_array):
        tc2 = tc.text[index]
        for x in range(len(tc.text)):
            return_array[index].append([])
    return return_array
def extract_daf(s):
    return_dict = {}
    return_dict["daf"]= getGematria(s)    
    return_dict["amud"]= "a" if u"." in s else "b"
    return return_dict
def get_daf_en(num):

    if num % 2 == 1:
        num = num / 2 + 2
        return str(num)+"a"

    else:
        num = num / 2 + 1
        return str(num)+"b"
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def remove_markers(s):
    s = re.sub(ur"<\d+>\S{1,4}\)<\d+>",u"",s)
    s = re.sub(ur"<\d+>",u"",s)
    s = re.sub(ur"\*+\)",u"",s)
    return s
def get_hebrew_name(title):
    return highest_fuzz(tractate_titles.keys(), title)
#bad experiences with fuzzy wuzzy's .process and unicode...
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match
def rng_post_term():
    term_obj = {
        "name": "Rav Nissim Goan",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Rav Nissim Goan",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'רב נסים גאון',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
#here starts methods for linking:

def dh_extract_method(some_string):
    first_sentence= remove_extra_space(re.split(ur"[\.:]",some_string)[0])
    if len(first_sentence.split())>8:
        return ' '.join(some_string.split()[:8])
    return first_sentence
def remove_extra_space(string):
    while u"  " in string:
        string = string.replace(u"  ",u" ")
    return string
def base_tokenizer(some_string):
    return filter(lambda(x): x!=u'',remove_extra_space(strip_nekud(some_string).replace(u"<b>",u"").replace(u"</b>",u"").replace(".","").replace(u"\n",u"")).split(u" "))
posting_term=False
posting_index = False
posting_text =False
linking = True

if posting_term:
    rng_post_term()
admin_links = []
site_links = []
for rc_file in os.listdir("files"):
    if ".txt" in rc_file:# and "01" in rc_file:
        current_tractate = RNG_Tractate(rc_file)
        admin_links.append(SEFARIA_SERVER+"/admin/reset/Rav_Nissim_Goan_on_"+current_tractate.en_tractate_name.replace(u" ",u"_"))
        site_links.append(SEFARIA_SERVER+"/Rav_Nissim_Goan_on_"+current_tractate.en_tractate_name.replace(u" ",u"_"))
        if posting_index:
            print "posting ",current_tractate.en_tractate_name," index..."
            current_tractate.make_tractate_index()
        if posting_text:
            print "posting ",current_tractate.en_tractate_name," text..."
            current_tractate.rc_post_text()
        if linking:
            print "linking",current_tractate.en_tractate_name,"..."
            current_tractate.rc_link()
        """
        for dindex, daf in enumerate(current_tractate.text):
            for cindex, comment in enumerate(daf):
                print dindex, cindex, comment
        """
        
print "Admin Links:"
for link in admin_links:
    print link
print "Site Links:"
for link in site_links:
    print link
