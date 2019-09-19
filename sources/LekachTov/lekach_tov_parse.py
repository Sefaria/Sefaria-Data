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
def clean_text_line(s):
    s = re.sub(ur'\$\s*\[.*?\]',u'',s)
    s = re.sub(ur'\%\s*\[.*?\]',u'',s)
    for match in re.findall(ur'^.*?\.',s):
        if u',' not in match:
            s=s.replace(match,u'<b>'+match+u'</b>')
    for match in re.findall(ur'~\(.*?\)',s):
        s=s.replace(match,u"""<i data-commentator="Notes and Corrections on Midrash Lekach Tov" data-order="{}"></i>""".format(getGematria(match)))
    
    return s
def clean_intro_line(s):
    for match in re.findall(ur'~\(.*?\)',s):
        s=s.replace(match,u"""<i data-commentator="Notes and Corrections on Midrash Lekach Tov" data-order="{}"></i>""".format(getGematria(match)))
    return s
def post_lt_index():
    # create index record
    record = SchemaNode()
    record.add_title('Midrash Lekach Tov on Esther', 'en', primary=True, )
    record.add_title(u'מדרש לקח טוב על אסתר', 'he', primary=True, )
    record.key = 'Midrash Lekach Tov on Esther'

    intro_node = JaggedArrayNode()
    intro_node.add_title('Introduction', 'en', primary = True)
    intro_node.add_title(u'הקדמה', 'he', primary = True)
    intro_node.key = 'Introduction'
    intro_node.depth = 1
    intro_node.addressTypes = ['Integer']
    intro_node.sectionNames = ['Paragraph']
    record.append(intro_node)
    
    #now we add text node
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True
    text_node.depth = 3
    text_node.addressTypes = ['Integer', 'Integer', 'Integer']
    text_node.sectionNames = ['Chapter','Verse','Comment']
    text_node.toc_zoom=2
    record.append(text_node)
    record.validate()

    index = {
        "title": 'Midrash Lekach Tov on Esther',
        "base_text_titles": [
          "Esther"
        ],
        "dependence": "Midrash",
        "collective_title": "Midrash Lekach Tov",
        "categories": ["Midrash","Aggadic Midrash","Midrash Lekach Tov"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def post_lt_term():
    term_obj = {
        "name": 'Midrash Lekach Tov',
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": 'Midrash Lekach Tov',
                "primary": True
            },
            {
                "lang": "he",
                "text": u'מדרש לקח טוב',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
def post_lt_note_term():
    term_obj = {
        "name": 'Notes and Corrections on Midrash Lekach Tov',
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": 'Notes and Corrections on Midrash Lekach Tov',
                "primary": True
            },
            {
                "lang": "he",
                "text": u'הערות ותיקונים על מדרש לקח טוב',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
def post_lt_text(posting_text=True,linking=False):
    with open('מדרש לקח טוב על אסתר.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))

    past_start=False
    intro_box=[]
    comment_text = make_perek_array("Esther")
    current_perek=None
    current_pasuk=None

    for line in lines:
        if u'כתוב בטוב צדיקים' in line:
            past_start=True
        if past_start and not_blank(line):
            for comment in line.replace(u'\n',u'').split(u':'):
                if re.search(ur'\$\s*\[.*?\]',comment):
                    current_perek = getGematria(re.search(ur'\$\s*\[.*?\]',comment).group())
                    #print "PEREK", current_perek
                if re.search(ur'%\s*\[.*?\]',comment):
                    current_pasuk = getGematria(re.search(ur'\%\s*\[.*?\]',comment).group())
                    #print "PASUK", current_pasuk
                if current_perek and current_pasuk and not_blank(clean_text_line(comment)):
                    comment_text[current_perek-1][current_pasuk-1].append(clean_text_line(comment+u':'))
                elif not_blank(clean_intro_line(comment)):
                    intro_box.append(clean_intro_line(comment)+':')
    """
    for pindex, paragraph in enumerate(intro_box):
        print pindex, paragraph
    """
    for pindex, perek in enumerate(comment_text):
        for paindex, pasuk in enumerate(perek):
            for cindex, comment in enumerate(pasuk):
                print pindex, paindex, cindex, comment
                print repr(comment)
    """
    """
    #1/0
    if posting_text:
        version = {
            'versionTitle': 'Sifre DeAgadeta, Vilna 1886',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001838260',
            'language': 'he',
            'text': intro_box
        }
        post_text_weak_connection('Midrash Lekach Tov on Esther, Introduction', version)
        version = {
            'versionTitle': 'Sifre DeAgadeta, Vilna 1886',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001838260',
            'language': 'he',
            'text': comment_text
        }
        post_text_weak_connection('Midrash Lekach Tov on Esther', version)
    if linking:
        if False:
            for perek_index,perek in enumerate(comment_text):
                for pasuk_index, pasuk in enumerate(perek):
                    for comment_index, comment in enumerate(pasuk):
                        link = (
                                {
                                "refs": [
                                         'Midrash Lekach Tov on Esther, {}:{}:{}'.format(perek_index+1, pasuk_index+1, comment_index+1),
                                         'Esther {}:{}'.format(perek_index+1, pasuk_index+1),
                                         ],
                                "type": "commentary",
                                "auto": True,
                                "generated_by": "sterling_lekach_tov_esther_linker"
                                })
                        post_link(link, weak_network=True)
        if True:
            for pindex, paragraph in enumerate(intro_box):
                for match in re.findall(ur'(?<=data-order=")\d*',paragraph):
                    link = {
                    'refs': ['Midrash Lekach Tov on Esther, Introduction {}'.format(pindex+1), 'Notes and Corrections on Midrash Lekach Tov on Esther 1:{}'.format(int(match))],
                    'type': 'commentary',
                    'inline_reference': {
                        'data-commentator': "Notes and Corrections on Midrash Lekach Tov",
                        'data-order': int(match)
                        },
                    "auto": True,
                    "generated_by": "sterling_leckach_tov_esther_note_linker"
                    }
                    post_link(link, weak_network=True)
            for pindex, perek in enumerate(comment_text):
                for paindex, pasuk in enumerate(perek):
                    for cindex, comment in enumerate(pasuk):
                        for match in re.findall(ur'(?<=data-order=")\d*', comment):
                            link = {
                            'refs': ['Midrash Lekach Tov on Esther {}:{}:{}'.format(pindex+1, paindex+1, cindex+1), 'Notes and Corrections on Midrash Lekach Tov on Esther {}:{}'.format(pindex+1,int(match))],
                            'type': 'commentary',
                            'inline_reference': {
                                'data-commentator': "Notes and Corrections on Midrash Lekach Tov",
                                'data-order': int(match)
                                },
                            "auto": True,
                            "generated_by": "sterling_leckach_tov_esther_note_linker"
                            }
                            post_link(link, weak_network=True)
                        
def post_notes_index():
    record = JaggedArrayNode()
    record.add_title('Notes and Corrections on Midrash Lekach Tov on Esther', 'en', primary = True)
    record.add_title(u'הערות ותיקונים על מדרש לקח טוב על אסתר', 'he', primary = True)
    record.key = 'Notes and Corrections on Midrash Lekach Tov on Esther'
    record.depth = 2
    record.addressTypes = ['Integer','Integer']
    record.sectionNames = ['Chapter','Comment']
    record.validate()

    index = {
        "title": 'Notes and Corrections on Midrash Lekach Tov on Esther',
        "categories": ["Midrash","Aggadic Midrash","Midrash Lekach Tov"],
        "base_text_titles": [u"Midrash Lekach Tov on Esther"],
        "collective_title": "Notes and Corrections on Midrash Lekach Tov",
        "dependence": "Commentary",
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def post_notes():
    with open('לקח טוב על אסתר - הערות.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    past_start=False
    note_box=[]
    all_chapters=[]
    for line in lines:
        if u'~' in line:
            past_start=True
        if past_start and not_blank(line):            
            for note in re.split(ur'~\s*\(\S*?\)',line):
                if u'$' not in note:
                    note_box.append(note)
            all_chapters.append(note_box)
            note_box=[]
    """
    for cindex, chapter in enumerate(all_chapters):
        for coindex, comment in enumerate(chapter):
            print cindex, coindex, comment
    """
    version = {
        'versionTitle': 'Sifre DeAgadeta, Vilna 1886',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001838260',
        'language': 'he',
        'text': all_chapters
    }
    post_text_weak_connection('Notes and Corrections on Midrash Lekach Tov on Esther', version)

    
def post_lk_category():
    add_category('Midrash Lekach Tov', ["Midrash","Aggadic Midrash",'Midrash Lekach Tov'], u'מדרש לקח טוב')
    
#post_lt_term()
#post_lk_category()
#post_lt_index()
#post_lt_note_term()
#post_notes_index()
#post_lt_text(False, True)

post_notes_index()
post_notes()

post_lt_text(False, True)
