# -*- coding: utf-8 -*-
import os
import re
import sys
import csv
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
import django
django.setup()
from sources.functions import *
import codecs
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from linking_utilities.dibur_hamatchil_matcher import *
import pdb

tractate_titles = {}
for tractate_title in library.get_indexes_in_category("Bavli"):
    he_title = library.get_index(tractate_title).get_title("he")
    tractate_titles[he_title]=tractate_title
def from_en_name_to_he_name(name):
    for key in tractate_titles.keys():
        if tractate_titles[key]==name:
            return key
class RC_Tractate:
    def __init__(self, file_name):
            self.file_name = file_name
            if 'R_' in file_name:
                self.en_tractate_name=re.search(ur'(?<=on ).*?(?=\.tsv)',file_name).group()
                self.he_tractate_name=from_en_name_to_he_name(self.en_tractate_name)
                self.parse_tractate2()
            else:
                self.he_tractate_name = get_hebrew_name(' '.join(file_name.split()[2:-1]).decode('utf8'))
                self.en_tractate_name = tractate_titles[self.he_tractate_name]
                self.parse_tractate()
    def make_tractate_index(self):
        en_title = self.en_tractate_name
        he_title = self.he_tractate_name
        record = JaggedArrayNode()
        record.add_title('Rabbeinu Chananel on '+en_title, 'en', primary=True)
        record.add_title(u"רבינו חננאל על מסכת"+u" "+he_title, 'he', primary=True)
        record.key = 'Rabbeinu Chananel on '+en_title
        record.depth = 2
        record.addressTypes = ['Talmud', 'Integer']
        record.sectionNames = ['Daf','Comment']
        record.validate()

        index = {
            "title":'Rabbeinu Chananel on '+en_title,
            "base_text_titles": [
               en_title
            ],
            "collective_title":"Rabbeinu Chananel",
            "dependence": "Commentary",
            "categories":["Talmud","Bavli","Commentary","Rabbeinu Chananel", get_mishnah_seder(en_title)],
            "schema": record.serialize()
        }
        post_index(index,weak_network=True)
        
    def parse_tractate(self):
        print self.en_tractate_name
        with open("files/"+self.file_name) as myFile:
            if u"Beit" not in self.en_tractate_name and u"Makk" not in self.en_tractate_name:
                lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
            else:
                lines = list(map(lambda x: x.decode("ISO 8859-8",'replace'), myFile.readlines()))
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
        for previous_amud_index, amud in enumerate(final_list[1:]):
            if len(amud)>0 and len(final_list[previous_amud_index])>0:
                if final_list[previous_amud_index][-1][-1]!=u"." and final_list[previous_amud_index][-1][-1]!=u":":
                    amud_split = re.findall(ur".*?[\.:]",amud[0])
                    previous_amud_dangler = re.split(ur"[\.:]",final_list[previous_amud_index][-1])[-1]
                    if len(amud_split)>1:
                        if len(previous_amud_dangler)>len(amud_split[0]):
                            #print "Pulled Back!"
                            if amud[0][-1]!=u"." and amud[0][-1]!=u":":
                                add_after.append(re.split(ur"[\.:]",amud[0])[-1])
                            final_list[previous_amud_index][-1]+=u" "+amud_split[0]
                            final_list[previous_amud_index+1][0]=''.join(amud_split[1:])
                            while len(add_after)>0:
                                final_list[previous_amud_index+1][0]+=add_after.pop()
                        else:
                            #print "Pushed Forward!"
                            final_list[previous_amud_index][-1]=''.join(re.findall(ur".*?[\.|:]",final_list[previous_amud_index][-1]))
                            final_list[previous_amud_index+1][0]=previous_amud_dangler+u" "+final_list[previous_amud_index+1][0]
                    """For case where the next amud doesn't have more than one period segment. For now, we do nothing.
                    else:
                        #print "MESSUP"
                        #print "Pulled Back!"
                        final_list[previous_amud_index][-1]+=u" "+amud_split[0]
                        final_list[previous_amud_index+1][0]=''.join(amud_split[1:])
                    """

                            
        final_list.insert(0,[])
        self.text = final_list
    def parse_tractate2(self):
        print 'parsing {}...'.format(self.en_tractate_name)
        with open('new_files/'+self.file_name) as tsvfile:
          reader = csv.reader(tsvfile, delimiter='\t')
          final_list = make_talmud_array(self.en_tractate_name)
          current_daf_ref={}
          next_row_goes_back=False
          for row in reader:
              daf_row=row[0].decode('utf','replace')
              text_row=row[1].decode('utf','replace')
              if next_row_goes_back:
                 next_row_goes_back=False 
                 if not_blank(text_row):
                     back_text=re.findall(ur'^.*?[\.:]',text_row)[0]
                     final_list[get_page(current_daf_ref["daf"],current_daf_ref["amud"])][-1]=final_list[get_page(current_daf_ref["daf"],current_daf_ref["amud"])][-1]+u' '+back_text.strip()
                     text_row.replace(back_text,u'')
                 else:
                     print "Problem here..."
                     print final_list[get_page(current_daf_ref["daf"],current_daf_ref["amud"])][-1]
              if not_blank(daf_row):
                  current_daf_ref=extract_daf(daf_row)
              if not_blank(text_row):
                  for comment in text_row.split(u':'):
                     if not_blank(comment):
                         final_list[get_page(current_daf_ref["daf"],current_daf_ref["amud"])].append(comment.strip())
                         
                  if text_row[-1]!=u'.' and text_row[-1]!=u':':
                     next_row_goes_back=True  
             
        final_list.insert(0,[])
        self.text = final_list
    def rc_post_text(self):
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': self.text
        }
        #post_text_weak_connection
        post_text_weak_connection('Rabbeinu Chananel on '+self.en_tractate_name, version)#,weak_network=True)# skip_links=True, index_count="on")
    def rc_link(self):
        for amud_index in range(1,len(TextChunk(Ref(self.en_tractate_name)).text)-1):
            if amud_index>0:
                #not every amud has a comment...
                try:
                    rc_ref=Ref('Rabbeinu Chananel on '+self.en_tractate_name+"."+get_daf_en(amud_index))
                    rc_chunk = TextChunk(rc_ref,"he")
                except:
                    print "No RC on Rabbeinu Chananel on ",self.en_tractate_name,".",get_daf_en(amud_index)
                    continue
                #for Rav Channanel, each "comment" contains comments on several passages.
                #therefore, link each comment to the whole amud
                print get_daf_en(amud_index)
                tractate_ref=Ref(self.en_tractate_name+"."+get_daf_en(amud_index))
                tractate_chunk = TextChunk(tractate_ref,"he")
                matches = match_ref(tractate_chunk,rc_chunk,base_tokenizer,dh_extract_method=dh_extract_method,verbose=True)
                if "comment_refs" in matches:
                    for link_index, (base, comment) in enumerate(zip(matches["matches"],matches["comment_refs"])):
                        if base:
                            if "-" in base.normal():
                                base=Ref(base.normal().split("-")[0])
                            print "MATCHED BC:",base,comment,base.normal()+"-"+tractate_ref.as_ranged_segment_ref().normal().split("-")[-1]
                            link = (
                                    {
                                    "refs": [
                                             base.normal()+"-"+tractate_ref.as_ranged_segment_ref().normal().split("-")[-1],
                                             comment.normal(),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_Rabbeinu_Chananel_linker"
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
                                    "generated_by": "sterling_Rabbeinu_Chananel_"+self.en_tractate_name+"_linker"
                                    })
                            post_link(link, weak_network=True)
                else:
                    print "UNMATCHED REF: ",rc_ref
                    link = (
                            {
                            "refs": [
                                     tractate_ref.as_ranged_segment_ref().normal(),
                                     rc_ref.normal(),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_Rabbeinu_Chananel_"+self.en_tractate_name+"_linker"
                            })
                    post_link(link, weak_network=True)
        """"
        for amud_index in range(1,len(TextChunk(Ref(self.en_tractate_name)).text)-1):
            if amud_index>0:
                #not every amud has a comment...
                try:
                    rc_ref = Ref('Rabbeinu Chananel on '+self.en_tractate_name+"."+get_daf_en(amud_index))
                except:
                    #print "No RC on Rabbeinu Chananel on ",self.en_tractate_name,".",get_daf_en(amud_index)
                    continue
                #for Rabbeinu Channanel, each "comment" contains comments on several passages.
                #therefore, link each comment to the whole amud
                tractate_ref = Ref(self.en_tractate_name+"."+get_daf_en(amud_index))
                for ref in rc_ref.all_segment_refs():
                    link = (
                            {
                            "refs": [
                                     tractate_ref.as_ranged_segment_ref().normal(),
                                     ref.normal(),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_Rabbeinu_Channanel_"+self.en_tractate_name+"_linker"
                            })
                    post_link(link, weak_network=True)
            """
def make_talmud_array(book):
    tc = TextChunk(Ref(book), "he")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
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
#bad experiences with fuzzy wuzzy's .process and unicode...
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match
seders = {'Seder Moed':u'סדר מועד','Seder Nezikin':u'סדר נזיקין'}
def post_talmud_categories():
    add_category('Rabbeinu Chananel', u"רבינו חננאל", ["Talmud","Bavli","Commentary",'Rabbeinu Chananel'])
    for seder in seders.keys():
        add_category(seder, seders[seder], ["Talmud","Bavli","Commentary",'Rabbeinu Chananel',seder])
def get_mishnah_seder(mishnah_title):
    if u"Mishnah" not in mishnah_title:
        mishnah_title="Mishnah "+mishnah_title
    for seder in seders.keys():
        indices = library.get_indexes_in_category(seder)
        if mishnah_title in indices:
            return seder
    return None
posting_cats = False
posting_index = True
posting_text = True
linking = False

if posting_cats:
    post_talmud_categories()
admin_links = []
site_links = []
for rc_file in os.listdir("files"):
    if ".txt" in rc_file and False:
        current_tractate = RC_Tractate(rc_file)
        admin_links.append(SEFARIA_SERVER+"/admin/reset/Rabbeinu_Chananel_on_"+current_tractate.en_tractate_name.replace(u" ",u"_"))
        site_links.append(SEFARIA_SERVER+"/Rabbeinu_Chananel_on_"+current_tractate.en_tractate_name.replace(u" ",u"_"))
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
for rc_file in os.listdir("new_files"):
    if ".tsv" in rc_file and "Avo" not in rc_file:
        current_tractate = RC_Tractate(rc_file)
        admin_links.append(SEFARIA_SERVER+"/admin/reset/Rabbeinu_Chananel_on_"+current_tractate.en_tractate_name.replace(u" ",u"_"))
        site_links.append(SEFARIA_SERVER+"/Rabbeinu_Chananel_on_"+current_tractate.en_tractate_name.replace(u" ",u"_"))
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
