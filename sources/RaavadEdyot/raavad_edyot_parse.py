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

def make_perek_array(book):
    #hit a bug with Pesach, fixed since then
    tc = TextChunk(Ref(book), "he") if "Pesac" not in book else TextChunk(Ref(book), "en")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    print "LEN",len(tc.text)
    for index, perek in enumerate(return_array):
        print "INDEX",index
        tc = TextChunk(Ref(book+" "+str(index+1)), "he") if "Pesac" not in book else TextChunk(Ref(book+" "+str(index+1)), "en")
        for x in range(len(tc.text)):
            return_array[index].append([])
    return return_array
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def raavad_post_index():   
    record = SchemaNode()
    record.add_title('Raavad on Mishnah Eduyot', 'en', primary=True)
    record.add_title(u'ראב"ד על משנה עדיות', 'he', primary=True)
    record.key = 'Raavad on Mishnah Eduyot'
    
    intro_node=JaggedArrayNode()
    intro_node.add_title('Introduction', 'en', primary=True)
    intro_node.add_title(u'הקדמה', 'he', primary=True)
    intro_node.key = 'Introduction'
    intro_node.depth = 1
    intro_node.addressTypes = ["Integer"]
    intro_node.sectionNames = ["Paragraph"]
    record.append(intro_node)
    
    
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True
    text_node.depth = 3
    text_node.toc_zoom = 2
    text_node.addressTypes = ['Perek', 'Mishnah','Integer']
    text_node.sectionNames = ['Chapter','Mishnah','Comment']
    text_node.heSectionNames= ["פרק",
    "משנה",
    "פסקה"
    ],
    record.append(text_node)
    
    record.validate()

    index = {
        "title":'Raavad on Mishnah Eduyot',
        "base_text_titles": [
          "Mishnah Eduyot"
        ],
        "dependence": "Commentary",
        "collective_title":"Raavad",
        "categories":["Mishnah","Commentary","Raavad"],
        "heCategories": ["משנה",
            "מפרשים",
"ראב\"ד"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def parse_raaved(posting=True):
    with open('ראבד_עדיות.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    tractate_array=make_perek_array("Mishnah Eduyot")
    current_chapter=0
    current_mishnah=0
    for line in lines:
        if not_blank(line):
            if u'@00' in line:
                current_chapter=getGematria(line.replace(u'פ',u''))
            elif u'@22' in line:
                current_mishnah=getGematria(line.split(u' ')[0])
            else:
                tractate_array[current_chapter-1][current_mishnah-1].append(clean_line(line))
    intro_box=[tractate_array[0][0].pop(0)]
    if posting:
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': intro_box
        }
        #post_text_weak_connection('Raavad on Mishnah Eduyot, Introduction', version)
        
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': tractate_array
        }
        post_text_weak_connection('Raavad on Mishnah Eduyot', version)
    return tractate_array
def raavad_link_text():
    raavad_text = parse_raaved(False)
    for perek_index,perek in enumerate(raavad_text):
        for mishna_index, mishna in enumerate(perek):
            for comment_index, comment in enumerate(mishna):
                link = (
                        {
                        "refs": [
                                 'Raavad on Mishnah Eduyot, {}:{}:{}'.format(perek_index+1, mishna_index+1, comment_index+1),
                                 'Mishnah Eduyot {}:{}'.format(perek_index+1, mishna_index+1),
                                 ],
                        "type": "commentary",
                        "auto": True,
                        "generated_by": 'sterling_raavad_edyot_linker'
                        })
                print link.get('refs')
                post_link(link, weak_network=True)
def clean_line(s):
    s = re.sub(ur'@44\S*\s*',u'',s)
    s = re.sub(ur'@66\s*\*(.*?)@77',ur'<small>[\1]</small>',s)
    s=re.sub(ur'\(\S\)',u'',s)
    s=re.sub(ur"@\d{1,3}",u"",s)
    if u'הקדמה' not in s and u'.' in s:
        if len(s.split(u'.')[0].split(u' '))<14 and u'תוספתא' not in s.split(u'.')[0] and s[s.index(u'.')+1]!=u')':
            s=u'<b>'+s[:s.index(u'.')+1]+u'</b>'+s[s.index(u'.')+1:]            
    return s
def add_cats():
    add_category('Raavad', ["Mishnah","Commentary","Raavad"],u"ראב\"ד")
#add_cats()
raavad_post_index()
#parse_raaved()
#raavad_link_text()