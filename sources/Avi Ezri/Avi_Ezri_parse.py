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
from data_utilities.dibur_hamatchil_matcher import *
import pdb

sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
def get_parsed_text():
    #with open('אבי-עזרי.txt') as myfile:
    with open('AE.txt') as myfile:
        text = re.sub(ur"[ \n]{2}","",''.join(list(map(lambda(x): x.decode('utf_8','replace'),myfile.readlines()))))
    #split chapters
    sefer_split = text.split(u"13#1511")[1:]
    full_text ={}
    for sefer_index, sefer in enumerate(sefer_split):
        sefer_list = make_perek_array(sefer_names[sefer_index])
        chapters = sefer.split(u"@09")
        for chapter in chapters:
            if not_blank(chapter)>0:
                chapter_index = getGematria(chapter.split(u"@73")[0])-1
                verses = chapter[chapter.index(u"3")+1:].split(u"@68")
                for verse in verses:
                    if not_blank(verse)>0:
                        verse_index = getGematria(verse.split(u"@73")[0])-1
                        #remove tag at beggining and split by comment:
                        comments  = verse[verse.index(u"3")+1:].split(u"@78")
                        #make DH's bold
                        comments = list(map(lambda(x): u"<b>"+x.replace(u"@58",u"</b>").replace(u"@48",u""),comments))
                        comments = [item for item in comments if item.strip()!=u"<b>"]
                        #comments = filter(lambda(x): x.strip()!=u"<b>",comments)
                        comments = list(map(lambda(x): x if isinstance(x, unicode) else x.decode('utf8',replace),comments))
                        try:
                            if len(sefer_list[chapter_index][verse_index])>1:
                                print "ERROR: Occupied! "+str(chapter_index)+" "+str(verse_index)
                            sefer_list[chapter_index][verse_index]=comments
                        except:
                            print "ERROR: OOR! "+sefer_names[sefer_index]+str(chapter_index)+" "+str(verse_index)
                            print verse
                            print "That one"
        full_text[sefer_names[sefer_index]]=sefer_list
    return full_text
            
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
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def print_text():
    #with open('אבי-עזרי.txt') as myfile:
    with open('AE.txt') as myfile:
        text = re.sub(ur"[ \n]{2}","",''.join(list(map(lambda(x): x.decode('utf_8','replace'),myfile.readlines()))))
    print text
    
def make_links(text):
    for key in text.keys():
        sefer_array = text[key]
        for perek_index,perek in enumerate(sefer_array):
            for pasuk_index, pasuk in enumerate(perek):
                for comment_index, comment in enumerate(pasuk):
                    #link to Torah and Ibn Ezra
                    link = (
                            {
                            "refs": [
                                     'Avi Ezer, {}, {}:{}:{}'.format(key, perek_index+1, pasuk_index+1, comment_index+1),
                                     '{} {}:{}'.format(key,perek_index+1, pasuk_index+1),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_avi_ezer_torah_linker"
                            })
                    print link.get('refs')
                    #post_link(link, weak_network=True)
                    #for Ibn Ezra, we try and match the actual comment:
                    base_ref = TextChunk(Ref('Ibn Ezra on {}, {}:{}'.format(key,perek_index+1, pasuk_index+1)),"he")
                    avi_ezri_ref = TextChunk(Ref('Avi Ezer, {}, {}:{}:{}'.format(key, perek_index+1, pasuk_index+1, comment_index+1)),"he")
                    Ibn_Ezra_links = match_ref(base_ref,avi_ezri_ref,base_tokenizer,dh_extract_method=dh_extract_method)
                    for base, comment in zip(Ibn_Ezra_links["matches"],Ibn_Ezra_links["comment_refs"]):
                        print "B",base,"C", comment
                        #post_link(link, weak_network=True)
#here starts methods for linking:
def filter(some_string):
    if re.search(ur'<b>(.*?)</b>', some_string) is None:
        return False
    else:
        return True

def dh_extract_method(some_string):
    return re.search(ur'<b>(.*?)</b>', some_string).group(1)

def base_tokenizer(some_string):
    return some_string.split(" ")
def get_links(sefer):
    base_ref = TextChunk(Ref(sefer),"he")
    avi_ezri_ref = TextChunk(Ref("Avi Ezri, "+str(sefer_ranges[book_index][1])+"-"+str(sefer_ranges[book_index][2])),"he")
    return match_ref(base_ref,akeida_ref,base_tokenizer,dh_extract_method=dh_extract_method)
    
text = get_parsed_text()


for sefer in text.keys():
    print key
    for chapter_index, chapter in enumerate(text[sefer]):
        for verse_index, verse in enumerate(chapter):
            for comment in verse:
                print str(chapter_index)+" "+str(verse_index)+" "+comment,type(comment)
"""

for key in text.keys():
    version = {
        'versionTitle': 'Avi Ezri',
        'versionSource': 'NO SOURCE SPECIFIED',
        'language': 'he',
        'text': text[key]
    }
    
    post_text_weak_connection('Avi Ezer, '+key, version)
"""
make_links(text)
