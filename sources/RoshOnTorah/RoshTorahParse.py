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

en_sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
he_sefer_names =  [u"בראשית",u"שמות" ,u"ויקרא",u"במדבר",u"דברים"]
title_dict = {u"בראשית":"Genesis",u"שמות":"Exodus",u"ויקרא":"Leviticus",u"במדבר":"Numbers",u"דברים":"Deuteronomy"}

def rosh_post_index():
    record = SchemaNode()
    record.add_title('Rosh on Torah', 'en', primary=True, )
    record.add_title(u'ראש על תורה', 'he', primary=True, )
    record.key = 'Rosh on Torah'


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
        "title":"Rosh on Torah",
        "base_text_titles": [
           "Genesis","Exodus","Leviticus","Numbers","Deuteronomy"
        ],
        "dependence": "Commentary",
        "collective_title":"Rosh",
        "categories":['Tanakh','Commentary'],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def rosh_post_text(posting=True):
    book_dict = {}
    with open("פירוש הראש על התורה.txt") as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    current_chapter = 1
    current_verse = 1
    sefer_index=-1
    sefer_array=None
    for line in lines:
        if not_blank(line):
            if u'~' in line:
                if sefer_array:
                    book_dict[en_sefer_names[sefer_index]]=sefer_array
                sefer_index+=1
                sefer_array=make_perek_array(en_sefer_names[sefer_index])
                
            elif u'@' in line:
                current_chapter=getGematria(line)
            elif u'#' not in line:
                if re.search(ur'^\(\S*\)',line):
                    current_verse=getGematria(re.search(ur'^\(\S*\)',line).group())
                sefer_array[current_chapter-1][current_verse-1].append(fix_markers(line))
    book_dict[en_sefer_names[sefer_index]]=sefer_array
    
    """
    for sefer in book_dict.keys():
        for cindex, chapter in enumerate(book_dict[sefer]):
            for vindex, verse in enumerate(chapter):
                for coindex, comment in enumerate(verse):
                    print sefer, cindex, vindex, coindex, comment
    """
    
    if posting:
        for sefer in book_dict.keys():
            version = {
                'versionTitle': 'Hadar Zekenim, Livorno, 1840',
                'versionSource': 'http://aleph.nli.org.il:80/F/?func=direct&doc_number=001091900&local_base=NNL01',
                'language': 'he',
                'text': book_dict[sefer]
            }
            print "posting "+sefer+" text..."
            post_text_weak_connection('Rosh on Torah, '+sefer, version)
            #post_text('Rosh on Torah, '+sefer, version, weak_network=True, skip_links=True, index_count="on")
    return book_dict
def make_links():
    textdict=rosh_post_text(False)
    for sefer in en_sefer_names:
        sefer_array = textdict[sefer]
        for perek_index,perek in enumerate(sefer_array):
            for pasuk_index, pasuk in enumerate(perek):
                for comment_index, comment in enumerate(pasuk):
                    link = (
                            {
                            "refs": [
                                     'Rosh on Torah, {}, {}:{}:{}'.format(sefer, perek_index+1, pasuk_index+1, comment_index+1),
                                     '{} {}:{}'.format(sefer,perek_index+1, pasuk_index+1),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_rosh_torah_linker"
                            })
                    print link.get('refs')
                    post_link(link, weak_network=True)
def fix_markers(s):
    s=re.sub(ur'^\(\S*\)\s*',u'',s)
    if len(s.split(u'.')[0].split(u' '))<6 and u'.' in s:
        s=u'<b>'+s[:s.index(u'.')+1]+'</b>'+s[s.index(u'.')+1:]
    return s
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
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
#rosh_post_index()
#rosh_post_text()
make_links()