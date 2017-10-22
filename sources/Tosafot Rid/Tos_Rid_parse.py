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

en_talmud = ["Berakhot","Shabbat","Eruvin","Pesachim","Rosh Hashanah","Yoma","Sukkah","Beitzah","Taanit","Megillah","Moed Katan",
"Chagigah","Yevamot","Ketubot","Nedarim","Nazir","Sotah","Gittin","Kiddushin","Bava Kamma","Bava Metzia","Bava Batra",
"Sanhedrin","Makkot","Shevuot","Avodah Zarah","Horayot","Zevachim","Menachot","Chullin","Bekhorot","Arakhin","Temurah",
"Keritot","Meilah","Tamid","Niddah"]

he_talmud = [u"ברכות",u"שבת",u"עירובין",u"פסחים",u"ראש השנה",u"יומא",u"סוכה",u"ביצה",
    u"תענית",u"מגילה",u"מועד קטן",u"חגיגה",u"יבמות",u"כתובות",u"נדרים",u"נזיר",u"סוטה",u"גיטין",
    u"קידושין",u"בבא קמא",u"בבא מציעא",u"בבא בתרא",u"סנהדרין",u"מכות",u"שבועות",u"עבודה זרה",
    u"הוריות",u"זבחים",u"מנחות",u"חולין",u"בכורות",u"ערכין",u"תמורה",u"כריתות",u"מעילה",u"תמיד",u"נדה"]
title_exceptions = {"megila mahadura 1":{"en_title":"Megillah First Recension",
                                        "he_title":u"מגילה מהדורא קמא",
                                        "masechet":"Megillah"},
                  "megila mahadura 2":{"en_title":"Megillah Second Recension",
                                        "he_title":u"מגילה מהדורא תנינא",
                                        "masechet":"Megillah"},
                  "eruvin mahadura 2":{"en_title":"Eruvin Second Recension",
                                        "he_title":u"עירובין מהדורא תנינא",
                                        "masechet":"Eruvin"},
                 "eruvin mahadura 3 4":{"en_title":"Eruvin Third & Fourth Recension",
                                      "he_title":u"עירובין מהדורא תליתאה ורביעאה",
                                      "masechet":"Eruvin"}
            }
def post_rid_term():
    term_obj = {
        "name": "Tosafot Rid",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Tosafot Rid",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'תוספות רי\"ד',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
def make_tractate_index(file_tractate_name):
    if file_tractate_name in title_exceptions:
        en_title = title_exceptions[file_tractate_name]["en_title"]
        he_title = title_exceptions[file_tractate_name]["he_title"]
        tractate_name = title_exceptions[file_tractate_name]["masechet"]
    else:
        en_title = process.extractOne(file_tractate_name, en_talmud)[0]
        tractate_name = process.extractOne(file_tractate_name, en_talmud)[0]
        he_title = he_talmud[en_talmud.index(tractate_name)]
        
    record = JaggedArrayNode()
    record.add_title('Tosafot Rid on '+en_title, 'en', primary=True)
    record.add_title(u'תוספות רי\"ד על'+' '+he_title, 'he', primary=True)
    record.key = 'Tosafot Rid on '+en_title
    record.depth = 2
    record.addressTypes = ['Talmud', 'Integer']
    record.sectionNames = ['Daf','Comment']
    record.validate()

    index = {
        "title":'Tosafot Rid on '+en_title,
        "base_text_titles": [
           tractate_name
        ],
        "dependence": "Commentary",
        "categories":["Talmud","Bavli","Commentary","Tosafot Rid"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def parse_tractate(file_tractate_name):
    if file_tractate_name in title_exceptions:
        tractate_name = title_exceptions[file_tractate_name]["masechet"]
    else:
        tractate_name = process.extractOne(file_tractate_name, en_talmud)[0]
    if "Ketubot" in tractate_name or "Gitt" in tractate_name:
        return parse_tractate_k(file_tractate_name)
    with open("tractates/"+file_tractate_name+".txt") as myFile:
        lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
    #if u"@22" in ''.join(lines):
    #    return no_marker_parse(tractate_name, lines)
    mesechet_array = make_talmud_array(tractate_name)
    past_start=False
    
    #dict contains daf and amud
    current_daf_ref = {}
    #subtract 2 since we start at 0, add one since range's range in non-inclusive
    final_list = [[] for x in range(len(TextChunk(Ref(tractate_name),"he").text)-1)]
    for line in lines:
        if u"@22" in line:
            if "daf" in current_daf_ref:
                old_daf = current_daf_ref["daf"]
            current_daf_ref = extract_daf(line)
            #sometimes, ע"ב has no daf
            if current_daf_ref["daf"]<2:
                current_daf_ref["daf"]=old_daf
            past_start=True
        elif past_start:
            if not_blank(line):
                final_list[get_page(current_daf_ref["daf"],current_daf_ref["amud"])].append(bold_dh(fix_markers(line)))
    #add blank to offset beggening:
    final_list.insert(0,[])
    return final_list

#ketubot and gittin need a seperate parse_text method
def parse_tractate_k(file_tractate_name):
    print "This is ",file_tractate_name
    tractate_name = process.extractOne(file_tractate_name, en_talmud)[0]
    past_start=False
    last_comment_was_fragment = False
    #dict contains daf and amud
    current_daf_ref = {}
    #subtract 2 since we start at 0, add one since range's range in non-inclusive
    final_list = [[] for x in range(len(TextChunk(Ref(tractate_name),"he").text)-1)]
    if "ketubot" in file_tractate_name:
        with open("tractates/"+file_tractate_name+".txt") as myFile:
            lines = list(map(lambda x: x.decode("ISO 8859-8",'replace'), myFile.readlines()))
        for line in lines:
            if u"@" in line:
                current_daf_ref = extract_daf_k(line)
                past_start=True
            elif past_start:
                for split_line in re.findall(ur".*?[:\n]",line):
                    split_line=split_line.replace(u"<פפפ>",u"")
                    if not_blank(split_line):
                        final_list[get_page(current_daf_ref["daf"],current_daf_ref["amud"])].append(split_line)   
    if "gittin" in file_tractate_name:
        with open("tractates/"+file_tractate_name+".txt") as myFile:
            lines = list(map(lambda x: x.decode("utf8",'replace'), myFile.readlines()))
        split_list=[]
        for line in lines:
            for split in re.split(ur"<\$.*?>",line):
                split_list.append(split)
        for line_b in split_list:
            print "Gittin",repr(line_b)
            if u"<דף>" in line_b:
                current_daf_ref = extract_daf_k(line_b)
                past_start=True
            elif past_start:
                for split in re.findall(ur".*?[:\n]",line_b):
                    split=split.replace(u"\n",u"").replace(u"<פפפ>",u"")
                    if not_blank(split):
                        final_list[get_page(current_daf_ref["daf"],current_daf_ref["amud"])].append(remove_tags(split))
    next_daf_has_previous_daf_comment = False
    super_final_list = [[] for x in range(len(TextChunk(Ref(tractate_name),"he").text)-1)]
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
                        #print previous_amud_index
                        #print "Pulled Back!"
                        if amud[0][-1]!=u"." and amud[0][-1]!=u":":
                            add_after.append(re.split(ur"[\.:]",amud[0])[-1])
                        #print amud_split[0]
                        final_list[previous_amud_index][-1]+=u" "+amud_split[0]
                        final_list[previous_amud_index+1][0]=None if len(amud_split)<1 else ''.join(amud_split[1:])
                        while len(add_after)>0:
                            final_list[previous_amud_index+1][0]+=add_after.pop()
                    else:
                        #print previous_amud_index
                        #print "Pushed Forward!"
                        final_list[previous_amud_index][-1]=''.join(re.findall(ur".*?[\.|:]",final_list[previous_amud_index][-1]))
                        final_list[previous_amud_index+1][0]=previous_amud_dangler+u" "+final_list[previous_amud_index+1][0]
    """
    add_after=[]
    for previous_amud_index, amud in enumerate(final_list[1:]):
        if len(amud)>0 and len(final_list[previous_amud_index])>0:
            if final_list[previous_amud_index][-1][-1]!=u":":
                amud_split = re.findall(ur".*?:",amud[0])
                if len(amud_split)>1:
                    #print "Pulled Back!"
                    if amud[0][-1]!=u"." and amud[0][-1]!=u":":
                        add_after.append(re.split(ur"[\.:]",amud[0])[-1])
                    final_list[previous_amud_index][-1]+=u" "+amud_split[0]
                    final_list[previous_amud_index+1][0]=''.join(amud_split[1:])
                    while len(add_after)>0:
                        final_list[previous_amud_index+1][0]+=add_after.pop()
    """
    super_final_list = [[] for x in range(len(TextChunk(Ref(tractate_name),"he").text)-1)]
    super_final_list.insert(0,[])
    for dindex, daf in enumerate(final_list):
        super_final_list[dindex]=filter(lambda(x): not_blank(x),final_list[dindex])
    for dindex, daf in enumerate(super_final_list):
        for cindex, comment in enumerate(daf):
            super_final_list[dindex][cindex]=bold_dh(comment)
            #print dindex,cindex,repr(comment),comment
    return super_final_list
def no_marker_parse(tractate_name, rid_text_input):
    #first, make masechet dapim array
    masechet_chunk = TextChunk(Ref(tractate_name),"he")
    masechet_by_amud = []
    for amud in masechet_chunk.text:
        masechet_by_amud.append(u' '.join(amud))
    #now, split into comments:
    rid_text = []
    for portion in rid_text_input:
        for split_part in portion.split(u":"):
            comment = split_part
    #now, make table of which daf each rid comment goes to
    #match table = def match_text(base_text, comments, dh_extract_method=lambda x: x,verbose=False,word_threshold=0.27,char_threshold=0.2,prev_matched_results=None,with_abbrev_ranges=False):
def remove_tags(s):
    return re.sub(ur"<111>.*?<222>",'',s)
def fix_markers(s):
    return re.sub(ur"\([א-ת]"+ur"{1,3}\)","",s.replace("@1","<small>(").replace("@3",")</small>"))
def bold_dh(some_string):
    splits = {
        "pi_split":some_string.split(u"פי"+u"'"),
        "pirush_split": some_string.split(u"פירוש"),
        "i_kashiya_split": some_string.split(u"אי קשיא"),
        "kashiya_li_split": some_string.split(u"קשיא לי"),
        "period_split": [some_string.split(u".")[0]+".",''],
        }
    #if re.match(ur".*?"+ur"ו?כו"+"\'?",some_string):
    if re.search(ur".*?כו"+ur"\'?(?=[ \.])",some_string):
        splits["chulei_split"]= [re.search(ur".*?כו?"+"\'?(?=[ \.])",some_string).group(),'']
    split_dh=get_smallest(splits)
    if len(split_dh.split(" "))<30:
        return u"<b>"+split_dh+u"</b>"+some_string[len(split_dh):]
    return some_string
def bold_before_period(s):
    if u"." in s:
        return u"<b>"+s[:s.index(u".")+1]+u"</b>"+s[s.index(u".")+1:]
    return s
def post_rid_text(file_tractate_name,rid_list):
    if file_tractate_name in title_exceptions:
        en_title = title_exceptions[file_tractate_name]["en_title"]
    else:
        en_title = process.extractOne(file_tractate_name, en_talmud)[0]
    version = {
        'versionTitle': 'Tosafot Rid',
        'versionSource': 'www.sefaria.org',
        'language': 'he',
        'text': rid_list
    }
    post_text_weak_connection('Tosafot Rid on '+en_title, version)
def link_tos_rid(file_tractate_name):
    if file_tractate_name in title_exceptions:
        en_title = title_exceptions[file_tractate_name]["en_title"]
        tractate_name = title_exceptions[file_tractate_name]["masechet"]
    else:
        en_title = process.extractOne(file_tractate_name, en_talmud)[0]
        tractate_name = process.extractOne(file_tractate_name, en_talmud)[0]
    matched_count = 0.00
    total = 0.00
    not_matched=[]
    for amud_index in range(1,len(TextChunk(Ref(tractate_name)).text)-1):
        tractate_chunk = TextChunk(Ref(tractate_name+"."+get_daf_en(amud_index)),"he")
        #sometimes, there is no Rif on a Daf:
        if amud_index>0:
            try:
                rid_chunk = TextChunk(Ref("Tosafot Rid on "+en_title+"."+get_daf_en(amud_index)),"he")
            except:
                print "ERRD"
                continue
            matches = match_ref(tractate_chunk,rid_chunk,
                base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=rid_filter,verbose=True,char_threshold=0.4)
            if "comment_refs" in matches:
                last_ref = Ref("Genesis").normal()
                for base, comment in zip(matches["matches"],matches["comment_refs"]):
                    print base,comment
                    if base:
                        link = (
                                {
                                "refs": [
                                         base.normal(),
                                         comment.normal(),
                                         ],
                                "type": "commentary",
                                "auto": True,
                                "generated_by": "sterling_tos_rid_linker"
                                })
                        last_ref = base.normal()
                        post_link(link, weak_network=True)
                        matched_count+=1
                    else:
                        not_matched.append(comment)
                        if last_ref!=u'Genesis':
                        #we link to last comment, assuming it's a continuation
                            link = (
                                    {
                                    "refs": [
                                             last_ref,
                                             comment.normal(),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_tos_rid_linker"
                                    })
                            post_link(link, weak_network=True)
                    total+=1
            else:
                not_matched.append(get_daf_en(amud_index))
                total+=1
    if total!=0:
        print "Ratio: "+str(matched_count/total)
    else:
        print "Ratio: No Matches..."
    print "Not Matched:"
    for nm in not_matched:
        print nm
    
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
def get_daf_en(num):

    if num % 2 == 1:
        num = num / 2 + 2
        return str(num)+"a"

    else:
        num = num / 2 + 1
        return str(num)+"b"
#return daf info given a line with format @22דף ב ע"ב
def extract_daf(s):
    return_dict = {}
    return_dict["daf"]= getGematria(s.replace(u"@22","").replace(u"דף",u"").replace(u"ע\"ב",u"").replace(u"ע\"א",u""))    
    return_dict["amud"]= "a" if u"ע\"א" in s else "b"
    return return_dict
def extract_daf_k(s):
    print "DAF REF ",s
    s = s.replace(u"דף","")
    return_dict = {}
    return_dict["daf"]= getGematria(s)    
    return_dict["amud"]= "a" if u"." in s else "b"
    return return_dict
        
def rid_filter(some_string):
    #asssume every piece of text has a DH
    print some_string
    if not_blank(some_string) and len(some_string.replace(u"<b>",u"").replace(u"</b>",u""))>4:
        return True
    return False 
def not_blank(s):
    while u" " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def remove_extra_space(s):
    while u"  " in s:
        s = s.replace("  "," ")
    return s
def dh_extract_method(some_string):
    some_string = remove_extra_space(some_string).replace(u"<b>","").replace(u"</b>","")
    splits = {
        "pi_split":some_string.split(u"פי"+u"'"),
        "pirush_split": some_string.split(u"פירוש"),
        "period_split": some_string.split(u"."),
        "chulei_split": some_string.split(u"כו"+"'")
        }
    split_dh=get_smallest(splits)
    if len(split_dh.split(u" "))<10 and len(split_dh.split(u" "))>1:
        dh = split_dh
    else:
        dh=u' '.join(some_string.split(u" ")[0:4])
    return dh
def get_smallest(dic):
    return_dh = ""
    keyp = ""
    smallest_so_far = int
    for key in dic.keys():
        if len(dic[key][0])<smallest_so_far:
            smallest_so_far=len(dic[key][0])
            return_dh = dic[key][0]
            keyp=key
    return return_dh
def base_tokenizer(some_string):
    some_string = remove_extra_space(some_string).replace("<b>","").replace("</b>","").replace(":","")
    return filter(not_blank,some_string.split(" "))
def print_text(file_name):
    with open("tractates/"+file_name) as my_file:
        lines = my_file.readlines()
    for line in lines:
        print "NEWLINE"
        print line
        print ''

posting_term=True
posting_index=True
posting_text=True
linking=True
admin_links = []
page_links = []
if posting_term:
    post_rid_term()
for findex, file in enumerate(os.listdir("tractates")):
    print "This is file: "+str(findex)
    if ".txt" in file and ("ketu" in file or "gittin" in file):
        file_tractate_name = file.replace(".txt","")
        if file_tractate_name in title_exceptions:
            link_name = title_exceptions[file_tractate_name]["en_title"]     
        else:
            link_name = process.extractOne(file_tractate_name, en_talmud)[0]  
        admin_links.append("localhost:8000/admin/reset/Tosafot Rid on "+link_name)
        page_links.append("http://proto.sefaria.org/Tosafot_Rid_on_"+link_name)
        if posting_index:
            print "Posting "+file_tractate_name+" index..."
            make_tractate_index(file_tractate_name)
        rid_list = parse_tractate(file_tractate_name)
        for dindex, daf in enumerate(rid_list):
            for cindex, comment in enumerate(daf):
                print dindex, cindex, comment
        if posting_text:
            "Posting "+file_tractate_name+"text..."
            post_rid_text(file_tractate_name,rid_list)
        if linking:
            link_tos_rid(file_tractate_name)
print "ADMIN LINKS:"
for link in admin_links:
    print link
print "PAGE LINKS:"
for link in page_links:
    print link

"""
        for previous_amud_index, amud in enumerate(final_list[1:]):
            if len(amud)>0 and len(final_list[previous_amud_index])>0:
                print previous_amud_index
                if final_list[previous_amud_index][-1][-1]!=u"." and previous_amud_index>0:
                    amud_split = re.findall(ur".*?\.",amud[0])
                    if len(amud_split)>1:
                        final_list[previous_amud_index][-1]+=u" "+amud_split[0]
                        final_list[previous_amud_index+1][0]=''.join(amud_split[1:])
"""

