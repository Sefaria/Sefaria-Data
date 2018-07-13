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
en_sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
he_sefer_names =  [u"בראשית",u"שמות" ,u"ויקרא",u"במדבר",u"דברים"]
title_dict = {u"בראשית":"Genesis",u"שמות":"Exodus",u"ויקרא":"Leviticus",u"במדבר":"Numbers",u"דברים":"Deuteronomy"}
def hk_post_category():
    term_obj = {
        "name": 'HaKtav VeHaKabalah',
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": 'HaKtav VeHaKabalah',
                "primary": True
            },
            {
                "lang": "he",
                "text": u'הכתב והקבלה',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
    add_category('HaKtav VeHaKabalah', u'הכתב והקבלה', ["Tanakh","Commentary","HaKtav VeHaKabalah"])
def hk_post_index():
    record = SchemaNode()
    record.add_title('HaKtav VeHaKabalah', 'en', primary=True, )
    record.add_title(u'הכתב והקבלה', 'he', primary=True, )
    record.key = 'HaKtav VeHaKabalah'
    
    #add node for introduction
    intro_node = JaggedArrayNode()
    intro_node.add_title("Introduction", 'en', primary = True)
    intro_node.add_title(u'מאמר התורה', 'he', primary = True)
    intro_node.key = "Introduction"
    intro_node.depth = 1
    intro_node.addressTypes = ['Integer']
    intro_node.sectionNames = ['Paragraph']
    record.append(intro_node)


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
    
    #add node for outro
    outro_node = JaggedArrayNode()
    outro_node.add_title("Postscript", 'en', primary = True)
    outro_node.add_title(u'הערה', 'he', primary = True)
    outro_node.key = "Postscript"
    outro_node.depth = 1
    outro_node.addressTypes = ['Integer']
    outro_node.sectionNames = ['Paragraph']
    record.append(outro_node)
    record.validate()

    index = {
        "title":"HaKtav VeHaKabalah",
        "base_text_titles": [
           "Genesis","Exodus","Leviticus","Numbers","Deuteronomy"
        ],
        "dependence": "Commentary",
        "categories":['Tanakh','Commentary','HaKtav VeHaKabalah'],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def hk_post_text():
    book_dict = {}
    for hk_file in os.listdir("files"):
        if ".txt" in hk_file:
            with open("files/"+hk_file) as myfile:
                lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
            in_commentary=False
            in_intro=False
            current_chapter = 1
            current_verse = 1
            sefer_array=None
            line_count=0
            for line in lines:
                line_count+=1
                if u'@01בראשית' in line or u'$ויקרא' in line:
                    in_commentary=True
                if u"START" in line:
                    in_intro=True
                elif in_commentary:
                    if u"@01" in line or u"$" in line:
                        if sefer_array:
                            book_dict[current_sefer]=sefer_array
                        current_sefer=title_dict[highest_fuzz(title_dict.keys(),line)]
                        sefer_array=make_perek_array(current_sefer)
                    elif u"@00" in line:
                        if getGematria(line)<current_chapter and getGematria(line)>1:
                            print "ERROR!!"
                            print "LINE: ",line_count
                            print line, current_sefer, current_chapter, current_verse
                        just_changed=True
                        current_chapter=getGematria(line)
                    elif u"@22" in line:
                        if getGematria(line)<current_verse and not just_changed:
                            print "ERROR!!"
                            print "LINE: ",line_count
                            print line, current_sefer, current_chapter, current_verse
                        current_verse=getGematria(line)
                        just_changed=False
                    elif not_blank(line):
                        sefer_array[current_chapter-1][current_verse-1].append(fix_markers(line))
            book_dict[current_sefer]=sefer_array
    for sefer in book_dict.keys():
        version = {
            'versionTitle': 'HaKtav VeHaKabbalah, Frankfurt 1880',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002009558',
            'language': 'he',
            'text': book_dict[sefer]
        }
        print "posting "+sefer+" text..."
        post_text_weak_connection('HaKtav VeHaKabalah, '+sefer, version)#, weak_network=True, skip_links=True, index_count="on")
def make_links():
    for sefer in en_sefer_names:
        sefer_array = TextChunk(Ref('HaKtav VeHaKabalah, '+sefer),'he').text
        for perek_index,perek in enumerate(sefer_array):
            for pasuk_index, pasuk in enumerate(perek):
                for comment_index, comment in enumerate(pasuk):
                    link = (
                            {
                            "refs": [
                                     'HaKtav VeHaKabalah, {}, {}:{}:{}'.format(sefer, perek_index+1, pasuk_index+1, comment_index+1),
                                     '{} {}:{}'.format(sefer,perek_index+1, pasuk_index+1),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_avi_ezer_torah_linker"
                            })
                    post_link(link, weak_network=True)
def fix_markers(s):
    return re.sub(ur"@[\d\*\)]*",u'',s.replace(u"@11",u"<b>").replace(u"@33",u"</b>"))
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match
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
#hk_post_category()
hk_post_index()
hk_post_text()
make_links()