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
import re
import csv
from fuzzywuzzy import fuzz

talmud_titles = {}
for tractate_title in library.get_indexes_in_category("Talmud"):
    he_title = library.get_index(tractate_title).get_title("he")
    talmud_titles[he_title]=tractate_title
def not_blank(s):
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);
def find_tractate_name(s):
    for tn in talmud_titles.keys():
        if tn in s:
            return talmud_titles[tn]
def clean_line(s):
    s=s.replace('\n','')
    return s
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
def dh_extract_method(some_string):
    some_string=some_string.replace('גמרא ','').replace(',','')
    if '@11' and '@33' in some_string:
        if len(re.search(r'(?<=@11).*?(?=@33)',some_string).group().split(' '))>4:
            return re.search(r'(?<=@11).*?(?=@33)',some_string).group()
    if 'וכו\'' in ' '.join(some_string.split(' ')[:10]):
        return some_string[:some_string.index('וכו\'')-1]
    return ' '.join(some_string.split(' ')[:8])

def remove_extra_space(string):
    while "  " in string:
        string = string.replace("  "," ")
    return string

def base_tokenizer(some_string):
    #return filter(lambda x: x!='',remove_extra_space(strip_nekud(some_string).replace("<b>","").replace("</b>","").replace(".","").replace("\n","")).split(" "))
    return remove_extra_space(strip_nekud(some_string).replace("<b>","").replace("</b>","").replace(".","").replace("\n","")).split(" ")

class Tractate:
    def __init__(self, tractate_name):
        self.he_tractate_name=tractate_name



text_dict={}
text_list=[]
tractate_list=[]


for rae_file in os.listdir('files'):
    if 'txt' in rae_file:    
        amud_box=[]
        with open('files/'+rae_file) as myFile:
            lines = list(map(lambda x: x, myFile.readlines()))
        current_tractate=None
        current_daf=None
        current_amud=None
        skipping=False
        for line in lines:
            if 'START SKIPPING' in line:
                skipping=True
            if 'STOP SKIPPING' in line:
                skipping=False
            if not skipping:
                if '@00' in line and len(line.split(' '))<6:
                    if find_tractate_name(line):
                        if current_amud and len(amud_box)>0:
                            text_list.append([current_tractate, current_daf, current_amud, amud_box])
                            amud_box=[]
                        current_tractate=find_tractate_name(line)
                        if current_tractate not in tractate_list:
                            tractate_list.append(current_tractate)
                        current_daf=None
                        current_amud=None
                if '@22' in line:
                    if current_amud and len(amud_box)>0 and (re.search(r'(?<=דף )\S+',line) or 'ע"א' in line or 'ע"ב' in line):
                        text_list.append([current_tractate, current_daf, current_amud, amud_box])
                        amud_box=[]
                    if re.search(r'(?<=דף )\S+',line):
                        current_daf=getGematria(re.search(r'(?<=דף )\S+',line).group())
                        current_amud='a'
                    if 'ע"א' in line:
                        current_amud='a'
                    if 'ע"ב' in line:
                        current_amud='b'
                elif current_tractate and current_daf and not_blank(line):
                    if '@11' in line or '@00' in line or len(amud_box)<1:
                        amud_box.append(clean_line(line))
                    else:
                        amud_box[-1]+='<br>'+clean_line(line)
        text_list.append([current_tractate, current_daf, current_amud, amud_box])

links = []
for tractate in tractate_list:
    myfile = open('output/RabbiEigerLinks_{}.tsv'.format(tractate),'w')
    myfile.close()
for set_of_comments in text_list:
    print('matching {}.{}{}...'.format(set_of_comments[0],set_of_comments[1],set_of_comments[2]))
    tractate_ref=Ref('{}.{}{}'.format(set_of_comments[0],set_of_comments[1],set_of_comments[2]))
    tractate_chunk = TextChunk(tractate_ref,"he")
    match_set = match_ref(tractate_chunk,set_of_comments[3],base_tokenizer,dh_extract_method=dh_extract_method,verbose=False)
    with open('output/RabbiEigerLinks_{}.tsv'.format(set_of_comments[0]),'a') as myfile:
        comments = set_of_comments[3]
        for c, comment in enumerate(comments):
            match = match_set["matches"][c]
            if match:
                comm = "Chidushei Rabbi Akiva Eiger on {}:{}".format(tractate_ref.normal(), c+1)
                links.append({"refs": [comm, match.normal()], "generated_by": "chidushei_akiva_eiger",
                              "auto": True, "type": "Commentary"})
post_link(links, server="http://sterling.sandbox.sefaria.org")
with open("links.json", 'w') as f:
    json.dump(links, f)
           #print "COMMENT\/"
           #print comment 
           # if base:
           #   myfile.write('{} {}{}\t{}\t{}\n'.format(set_of_comments[0],set_of_comments[1],set_of_comments[2],base,comment.encode('utf','replace')))
           # else:
           #   myfile.write('{} {}{}\tNULL\t{}\n'.format(set_of_comments[0],set_of_comments[1],set_of_comments[2],comment.encode('utf','replace')))
           #
    
    """
    if "comment_refs" in matches:
        for link_index, (base, comment) in enumerate(zip(matches["matches"],matches["comment_refs"])):
            if base:
                if "-" in base.normal():
                    base=Ref(base.normal().split("-")[0])
                print "MATCHED BC:",base,comment,base.normal()+"-"+tractate_ref.as_ranged_segment_ref().normal().split("-")[-1]
                link = (
                        {
                        "refs": [
                                 base.normal(),
                                 comment.normal(),
                                 ],
                        "type": "commentary",
                        "auto": True,
                        "generated_by": "sterling_Tosafot_HaRosh_linker"
                        })
                post_link(link, weak_network=True)
    """

        
"""
from beggining of vol iii:  
מקרא:
@00 כותרת
@01 כותרת משנה
@11 תחילת קטע
@22 דף
@33 טקסט רגיל אחרי תחילת קטע
@44 תחילת קטע אמצע
@55 טקסט רגיל אחרי תחילת קטע אמצע 
@66 מודגש
@77 סוף מודגש
@88 אות לפני תחילת קטע
@99 כותר סיום


@00חידושי רבי עקיבא אייגר 
"""