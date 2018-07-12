# -*- coding: utf-8 -*-
import sys
import os
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
import re
import data_utilities
from sources import functions
import urllib2
import json
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from data_utilities.dibur_hamatchil_matcher import *
import pdb
def get_ch_title_dic():
    ch_dict = json.loads(urllib2.urlopen("https://www.sefaria.org/api/v2/raw/index/Duties_of_the_Heart").read())
    en_titles = []
    he_titles = []
    final_dict = {}
    for title_node in ch_dict["schema"]["nodes"]:
        for title in title_node["titles"]:
            if title["lang"]=="en":
                en_titles.append(title["text"])
            elif title["lang"]=="he":
                he_titles.append(title["text"])
    for he_title, en_title in zip(he_titles, en_titles):
        final_dict[he_title]=en_title
    return final_dict
ch_titles = get_ch_title_dic()
def ch_post_term(comm_name):
    term_obj = {
        "name": comm_name,
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": comm_name,
                "primary": True
            },
            {
                "lang": "he",
                "text": com_dic[comm_name]["he_title"],
                "primary": True
            }
        ]
    }
    post_term(term_obj)

def ch_index_post(com_name):
    section_titles = get_section_titles(com_name)
    # create index record
    com_record = com_dic[com_name]
    
    record = SchemaNode()
    record.add_title(com_name, 'en', primary=True)
    record.add_title(com_record["he_title"], 'he', primary=True)
    record.key = com_name
    #Tov Levanon has no commentator's intro
    if "Tov haLevanon" not in com_name:
        "HINTRO ",com_name
        #add commentor's intro node
        intro_node = JaggedArrayNode()
        intro_node.add_title(com_record["introduction_name_en"], 'en', primary=True)
        intro_node.add_title(com_record["introduction_name_he"], 'he', primary=True)
        intro_node.key = com_record["introduction_name_en"]
        intro_node.depth = 1
        intro_node.addressTypes = ['Integer']
        intro_node.sectionNames = ['Paragraph']
        record.append(intro_node)
    
    # add nodes for author's introduction and rest of sections
    for title_index, title in enumerate(section_titles):
        #author's intro handled differently
        if title_index==0:
            intro_node = JaggedArrayNode()
            intro_node.add_title(title["en_title"],"en",primary=True)
            intro_node.add_title(title["he_title"],"he",primary=True)
            intro_node.key = title["en_title"]
            intro_node.depth = 1
            intro_node.addressTypes = ['Integer']
            intro_node.sectionNames = ['Comment']
            record.append(intro_node)
        else:
            section_node = SchemaNode()
            section_node.add_title(title["en_title"],"en",primary=True)
            section_node.add_title(title["he_title"],"he",primary=True)
            section_node.key = title["en_title"]
            #first we make node for intro
            intro_node = JaggedArrayNode()
            intro_node.add_title("Introduction", 'en', primary=True)
            intro_node.add_title(u"הקדמה", 'he', primary=True)
            intro_node.key = "Introduction"
            intro_node.depth = 1
            intro_node.addressTypes = ['Integer']
            intro_node.sectionNames = ['Comment']
            section_node.append(intro_node)
        
            #now add chapters, or default
            text_node = JaggedArrayNode()
            text_node.key = "default"
            text_node.default = True
            text_node.depth = 2
            text_node.addressTypes = ['Integer', 'Integer']
            text_node.sectionNames = ['Chapter','Comment']
            section_node.append(text_node)
        
            record.append(section_node)


    record.validate()

    index = {
        "title":com_name,
        "base_text_titles": [
           "Duties of the Heart"
        ],
        "dependence": "Commentary",
        "categories":['Philosophy','Commentary',com_name,'Duties of the Heart'],
        "schema": record.serialize(),
        "collective_title":com_name
        }
    functions.post_index(index,weak_network=True)
    
def get_section_titles(com_name):
    with open(com_dic[com_name]["file_name"]) as myfile:
        lines = list(map(lambda(x): x.decode('utf8','replace'),myfile.readlines()))
    com_titles = []
    in_intro=False
    for line in lines:
        if u"@00הקדמה" in line:
            in_intro=True
        if in_intro:
            if u"@00" in line:
                ch_title = best_ch_fuzz(line)
                com_titles.append({"he_title":ch_title, "en_title":ch_titles[ch_title]})
    return com_titles
def ch_post_text(key):
    section_titles = get_section_titles(key)
    for title in section_titles:
        print "SECTITLE: ",title
    """
    section_chapters = {}
    for title in section_titles:
        section_chapters[title] = [[] for x in range(len(TextChunk(Ref("Duties of the Heart, "+section_titles),"en")))]
    #add intro seperate
    section_chapters[com_dic[key]["introduction_name_en"]]=[[] for x in range(len(TextChunk(Ref("Duties of the Heart, "+com_dic[key]["introduction_name_en"]),"en")))]
    """
    with open(com_dic[key]["file_name"]) as myfile:
        lines = list(map(lambda(x): x.decode('utf8','replace'), myfile.readlines()))
    chapter_box=[]
    section_box=[]
    comms_intro = []
    current_chapter = 0
    section_title_index = 0
    in_intro = False
    for line in lines:
        if u"@00הקדמה" in line:
            in_intro=True
        if not in_intro:
            if u"@00" not in line:
                if u"@22" in line:
                    line = u"<b>"+line+u"</b>"
                comms_intro.append(re.sub(ur"@\d{1,3}","",line))
        if in_intro:
            if u"@00" in line: 
                print key+ " LINE: "+line
                if len(section_box)>0 or len(chapter_box)>0:
                    #introduction has no chapters
                    section_box.append(chapter_box)
                    print key, section_titles[section_title_index]["en_title"]
                    """
                    for cindex, chapter in enumerate(section_box):
                        for pindex, paragraph in enumerate(chapter):
                            print cindex, pindex, paragraph
                    """
                    section_title = section_titles[section_title_index]["en_title"]
                    print "^^",section_title
                    #introduction has no chapters or introduction:
                    if section_title_index==0:
                        version = {
                            'versionTitle': 'Chovat Halevavot, Warsaw 1875',
                            'versionSource':'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001188038',
                            'language': 'he',
                            'text': chapter_box
                        }
                        print "posting "+section_title
                        post_text_weak_connection(key+', '+section_title, version)
                    else:
                        version = {
                            'versionTitle': 'Chovat Halevavot, Warsaw 1875',
                            'versionSource':'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001188038',
                            'language': 'he',
                            'text': section_box[1:] #first item is intro
                        }
                        print "posting text,"+section_title
                        post_text_weak_connection(key+', '+section_title, version)
                        version = {
                            'versionTitle': 'Chovat Halevavot, Warsaw 1875',
                            'versionSource':'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001188038',
                            'language': 'he',
                            'text': section_box[0]
                        }
                        print "posting introduction,"+section_title
                        post_text_weak_connection(key+', '+section_title+', Introduction', version)
                    section_title_index+=1                                              
                    section_box=[]
                    chapter_box = []
                    
            elif u"@22" in line and u"IGNORE" not in line:
                for x in range(getGematria(line.replace(u"פרק",u""))-current_chapter-1):
                    print "MISSING OM! ",line, " ", key, " ",section_title
                    section_box.append([])
                current_chapter = getGematria(line.replace(u"פרק",u""))
                section_box.append(chapter_box)
                chapter_box = []
                print "THIS IS CHAPTER ",current_chapter
                print "and we are ",len(section_box)," long"
            elif not_blank(line):
                chapter_box.append(re.sub(ur"@\d{1,3}",u"",line.replace(u"@11",u"<b>").replace(u"@33",u"</b>")))
    #post last chapter
    section_box.append(chapter_box)
    chapter_box = []
    print key, section_titles[section_title_index]["en_title"]
    
    for cindex, chapter in enumerate(section_box):
        for pindex, paragraph in enumerate(chapter):
            print cindex, pindex, paragraph
    
    section_title = section_titles[section_title_index]["en_title"]
    print "^^",section_title
    version = {
        'versionTitle': 'Chovat Halevavot, Warsaw 1875',
        'versionSource':'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001188038',
        'language': 'he',
        'text': section_box[1:] #first item is intro
    }
    print "posting text,"+section_title
    post_text_weak_connection(key+', '+section_title, version)
    version = {
        'versionTitle': 'Chovat Halevavot, Warsaw 1875',
        'versionSource':'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001188038',
        'language': 'he',
        'text': section_box[0]
    }
    print "posting introduction,"+section_title
    post_text_weak_connection(key+', '+section_title+', Introduction', version)
    #Tov Levanon has no commentator's intro
    if "Tov haLevanon" not in key:
        #now, post introductions to commentaries
        version = {
            'versionTitle': 'Chovat Halevavot, Warsaw 1875',
            'versionSource':'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001188038',
            'language': 'he',
            'text': comms_intro
        }
        print "posting comms intro"
        post_text_weak_connection(key+", "+com_dic[key]["introduction_name_en"], version)

def make_links(key):
    matched=0.00
    total=0.00
    errored = []
    not_machted = []
    sample_Ref = Ref("Genesis 1")
    for section_index, section in enumerate(get_section_titles(key)):
        last_not_matched = []
        #first section is intro, so no chapters...
        if section_index==0:
            last_matched = Ref('Duties of the Heart, {} 1'.format(section["en_title"]))
            base_chunk = TextChunk(Ref('Duties of the Heart, {}'.format(section["en_title"])),"he")
            com_chunk = TextChunk(Ref('{}, {}'.format(key, section["en_title"])),"he")
            ch_links = match_ref(base_chunk,com_chunk,base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=_filter)
            print "KEYS:"
            for key_thing in ch_links.keys():
                print key_thing
            #pdb.set_trace()
            for link_index, (base, comment) in enumerate(zip(ch_links["matches"],ch_links["comment_refs"])):
                total+=1
                print "B",base,"C", comment
                if base:
                    link = (
                            {
                            "refs": [
                                     base.normal(),
                                     comment.normal(),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_"+key.replace(" ","_")+"_linker"
                            })
                    post_link(link, weak_network=True)    
                    matched+=1
                    
                    while len(last_not_matched)>0:
                        print "we had ", last_matched.normal()
                        print "we have ", base.normal()
                        print "so, we'll do ",last_matched.normal()+"-"+base.ending_ref().normal_last_section()
                        link = (
                                {
                                "refs": [
                                         last_matched.normal()+"-"+base.ending_ref().normal_last_section(),
                                         last_not_matched.pop().normal(),
                                         ],
                                "type": "commentary",
                                "auto": True,
                                "generated_by": "sterling_"+key.replace(" ","_")+"_linker"
                                })
                        post_link(link, weak_network=True)
                        matched+=1
                        
                    last_matched=base
                       
                else:
                    not_machted.append('{}, {} Introduction'.format(key, section["en_title"]))
                    last_not_matched.append(comment.starting_ref())
                    if link_index==len(ch_links["matches"])-1:
                        print "NO LINKS LEFT!"
                        print "we had ", last_matched.normal()
                        print "so, we'll do ",last_matched.normal()+"-"+str(len(base_chunk.text))
                        while len(last_not_matched)>0:
                            link = (
                                    {
                                    "refs": [
                                             last_matched.normal()+"-"+str(len(base_chunk.text)),
                                             last_not_matched.pop().normal(),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_"+key.replace(" ","_")+"_linker"
                                    })
                            post_link(link, weak_network=True)
                            matched+=1
                         
        #for other sections, do each chapter seperate:
        else:
            indices = [q for q in range(1, len(TextChunk(Ref("Duties of the Heart, "+section["en_title"]),"en").text)+1)]
            indices.insert(0, "Introduction")
            #for chapter in range(1, len(TextChunk(Ref("Duties of the Heart, "+section["en_title"]),"en").text)+1):
            for chapter in indices:
                last_matched = Ref('Duties of the Heart, {}, {} 1'.format(section["en_title"],chapter))
                base_chunk = TextChunk(Ref('Duties of the Heart, {}, {}'.format(section["en_title"],chapter)),"he")
                com_chunk = TextChunk(Ref('{}, {}, {}'.format(key, section["en_title"], chapter)),"he")
                ch_links = match_ref(base_chunk,com_chunk,base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=_filter)
                if "comment_refs" in ch_links:
                    for link_index, (base, comment) in enumerate(zip(ch_links["matches"],ch_links["comment_refs"])):
                        total+=1
                        print "B",base,"C", comment
                        if base:
                            link = (
                                    {
                                    "refs": [
                                             base.normal(),
                                             comment.normal(),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_"+key.replace(" ","_")+"_linker"
                                    })
                            post_link(link, weak_network=True)    
                            matched+=1
                            
                            while len(last_not_matched)>0:
                                link = (
                                        {
                                        "refs": [
                                                 last_matched.normal()+"-"+base.ending_ref().normal_last_section(),
                                                 last_not_matched.pop().normal(),
                                                 ],
                                        "type": "commentary",
                                        "auto": True,
                                        "generated_by": "sterling_"+key.replace(" ","_")+"_linker"
                                        })
                                post_link(link, weak_network=True)
                                matched+=1
                        
                            last_matched=base.starting_ref()   
                        else:
                            not_machted.append('{}, {} Chapter {}'.format(key, section["en_title"], chapter))
                            last_not_matched.append(comment)
                            if link_index==len(ch_links["matches"])-1:
                                print "NO LINKS LEFT!"
                                print "we had ", last_matched.normal()
                                print "so, we'll do ",last_matched.normal()+"-"+str(len(base_chunk.text))
                                while len(last_not_matched)>0:
                                    link = (
                                            {
                                            "refs": [
                                                     last_matched.normal()+"-"+str(len(base_chunk.text)),
                                                     last_not_matched.pop().normal(),
                                                     ],
                                            "type": "commentary",
                                            "auto": True,
                                            "generated_by": "sterling_"+key.replace(" ","_")+"_linker"
                                            })
                                    post_link(link, weak_network=True)
                                    matched+=1
                            
                else:
                    not_machted.append('{}, {} Chapter {}'.format(key, section["en_title"], chapter))
                    
    pm = matched/total
    print "Result is:",matched,total
    print "Percent matched: "+str(pm)
    print "Not Matched:"
    for nm in not_machted:
        print nm
#here starts methods for linking:
def _filter(some_string):
    if re.search(ur'<b>(.*?)</b>', some_string) is None:
        return False
    else:
        return True

def dh_extract_method(some_string):
    #print "DH!:",some_string
    return re.search(ur'<b>(.*?)</b>', some_string).group(1)

def base_tokenizer(some_string):
    return filter(lambda(x): x!=u'',remove_extra_spaces(some_string.replace(u"<b>",u"").replace(u"</b>",u"").replace(u".",u"")).split(" "))
def remove_extra_spaces(string):
    string = re.sub(ur"\. $",u".",string)
    while u"  " in string:
        string=string.replace(u"  ",u" ")
    return string
def not_blank(s):
    while u" " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def best_ch_fuzz(title):
    highest_ratio = 0
    best_match = u''
    for key in ch_titles.keys():
        if fuzz.ratio(title,key)>highest_ratio:
            best_match=key
            highest_ratio=fuzz.ratio(title,key)
    return best_match
posting_term = False
posting_index = True
posting_text=True
linking = True
com_dic = {"Tov haLevanon":{"he_title":u"טוב הלבנון",
                           "file_name":"חובת הלבבות לב לבנון.txt",
                           "introduction_name_he":u"הקדמת המבאר",
                           "introduction_name_en":"Commentor's Introduction"},
            "Pat Lechem":{"he_title":u"פת לחם",
                        "file_name":"חובת הלבבות פת לחם.txt",
                        "introduction_name_he":u"הקדמת המבאר",
                        "introduction_name_en":"Introduction to Commentary"},
            "Marpeh la'Nefesh":{"he_title":u"מרפא לנפש",
                                "file_name":"חובת הלבבות מרפא לנפש.txt",
                                "introduction_name_he":u"הקדמת המפרש",
                                 "introduction_name_en":"Introduction to Commentary"}}    
admin_urls = []
site_urls = []     
for key in com_dic.keys():
    if "e" in key:
        print key
        admin_urls.append("proto.sefaria.org/admin/reset/"+key)
        site_urls.append("proto.sefaria.org/"+key)
        if posting_term:
            ch_post_term(key)
        if posting_index:
            ch_index_post(key)
        if posting_text:
            ch_post_text(key)
        if linking:
            make_links(key)
print "Admin urls:"
for url in admin_urls:
    print url
print "Site urls:"
for url in site_urls:
    print url        
    