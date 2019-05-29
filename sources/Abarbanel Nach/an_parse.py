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
import difflib


start_expressions=[u'הפרשה',u'פרשה',u'נבואה',u'הנבואה',u'פרשת',u'נבואת']
aleph_beis=ur'אב'
name_dict={}
for text in library.get_indexes_in_category('Tanakh'):
    name_dict[library.get_index(text).get_title('he')]=text
prophet_list=[]
for text in library.get_indexes_in_category('Prophets'):
    prophet_list.append(text)

def file_name_to_sefer(file_name):
    for name in name_dict.keys():
        if ' '+name in file_name.decode('utf8','replace'):
            return name
class megilah:
    def __init__(self, file_name):
        self.file_name = 'files/{}'.format(file_name)
        self.he_name = file_name_to_sefer(file_name)
        self.en_name = name_dict[self.he_name]
        self.has_intro=self.intro_check()
    def intro_check(self):
        with open(self.file_name) as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        for line in lines:
            if not_blank(line):
                if u'הקדמה' in line and u'פרק' not in line:
                    return True
                else:
                    return False
    def post_ab_index(self):
        if self.has_intro:
            record = SchemaNode()
            record.add_title("Abarbanel on "+self.en_name, 'en', primary=True)
            record.add_title(u'אברבנאל על'+' '+self.he_name, 'he', primary=True)
            record.key = "Abarbanel on "+self.en_name
            
            intro_node = JaggedArrayNode()
            intro_node.add_title("Introduction", 'en', primary = True)
            intro_node.add_title("הקדמה", 'he', primary = True)
            intro_node.key = "Introduction"
            intro_node.depth = 1
            intro_node.addressTypes = ['Integer']
            intro_node.sectionNames = ['Paragraph']
            record.append(intro_node)
            
            text_node = JaggedArrayNode()
            text_node.key = "default"
            text_node.default = True
            text_node.depth = 3
            text_node.toc_zoom = 2
            text_node.addressTypes = ['Integer', 'Integer','Integer']
            text_node.sectionNames = ['Chapter','Verse','Comment']
            record.append(text_node)
        else:
            record = JaggedArrayNode()
            record.add_title("Abarbanel on "+self.en_name, 'en', primary=True)
            record.add_title(u'אברבנאל על'+' '+self.he_name, 'he', primary=True)
            record.key = "Abarbanel on "+self.en_name
            record.depth = 3
            record.toc_zoom = 2
            record.addressTypes = ["Integer", "Integer","Integer"]
            record.sectionNames = ["Chapter", "Verse", "Comment"]
    
        record.validate()
        
        cat = "Prophets" if self.en_name in prophet_list else "Writings"
        print "posting {} index..".format(self.en_name)
        index = {
            "title":"Abarbanel on "+self.en_name,
            "base_text_titles": [
              self.en_name
            ],
            "dependence": "Commentary",
            "collective_title":"Abarbanel",
            "categories":["Tanakh","Commentary","Abarbanel",cat],
            "schema": record.serialize()
        }
        post_index(index,weak_network=True)
    def post_ab_text(self, posting=True):
        with open(self.file_name) as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        text_array = make_perek_array(self.en_name)
        intro_box=[]
        in_intro=False
        current_chapter=1
        current_verse=1
        for line in lines:
            if u'@' in line:
                if u'פרק' in line:
                    current_chapter=getGematria(re.search(ur'(?<=פרק ).*',line).group())
                    current_verse=1
                    in_intro=False
                elif u'הקדמה' in line:
                    in_intro=True
            elif not_blank(line):
                if in_intro:
                    intro_box.append(line)
                else:
                    if re.search(ur'^\s*\([א-ת- ]{1,15}\)',line):
                        current_verse=getGematria(re.search(ur'^\([א-ת- ]+\)',line).group().split(u'-')[0])
                    #try:
                    if checking:
                        #print '{} {}:{}:{}\n'.format(self.en_name, current_chapter, current_verse,len(text_array[current_chapter-1][current_verse-1])+1)
                        #print line
                        for s in start_expressions:
                            if re.search(ur'^{} '.format(s),line) and len(text_array[current_chapter-1][current_verse-1])>0:
                                print "CAUGHT"
                                with open("Abarbanel_errors.txt", "a") as f:
                                    f.write('{} {}:{}:{}\n'.format(self.en_name, current_chapter, current_verse,len(text_array[current_chapter-1][current_verse-1])+1)) 
                                    f.write('{}\n\n'.format(line.encode('utf8','replace')))
                    text_array[current_chapter-1][current_verse-1].append(clean_line(line))
                    """
                    except:
                        print "ERR",self.en_name
                        print current_chapter, current_verse
                        print line
                        0/0
                    """
        self.text=text_array

        if posting:
            if len(intro_box)>0:
                version = {
                    'versionTitle': "Abarbanel, Tel Aviv 1960",
                    'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?docid=NNL_ALEPH001080676&context=L&vid=NLI&search_scope=Local&tab=default_tab&lang=iw_IL',
                    'language': 'he',
                    'text': intro_box
                }
                print "posting {} intro...".format(self.en_name)
                post_text_weak_connection("Abarbanel on {}, Introduction".format(self.en_name), version)
            
            version = {
                'versionTitle': "Abarbanel, Tel Aviv 1960",
                'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?docid=NNL_ALEPH001080676&context=L&vid=NLI&search_scope=Local&tab=default_tab&lang=iw_IL',
                'language': 'he',
                'text': text_array
            }
            print "posting {} text...".format(self.en_name)
            post_text_weak_connection("Abarbanel on "+self.en_name, version)
    def ab_link(self):
        self.post_ab_text(False)
        for perek_index,perek in enumerate(self.text):
            for pasuk_index, pasuk in enumerate(perek):
                for comment_index, comment in enumerate(pasuk):
                    link = (
                            {
                            "refs": [
                                     'Abarbanel on {}, {}:{}:{}'.format(self.en_name, perek_index+1, pasuk_index+1, comment_index+1),
                                     '{} {}:{}'.format(self.en_name,perek_index+1, pasuk_index+1),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_Abarbanel_linker"
                            })
                    post_link(link, weak_network=True)
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def clean_line(s):
    pre=s
    s=re.sub(ur'\(ד\"ה ([{}]\')'.format(aleph_beis),ur'\(דברי הימים \1',s)
    s=re.sub(ur'דברי\s*-\s*הימים',u'דברי הימים',s)
    s=re.sub(ur'[^א-ת .:(),?\'\-"\r\n;\[\]!]',u'',s)
    """
    if s!=pre:
        print pre
        print s
    for i,s in enumerate(difflib.ndiff(pre, s)):
        if s[0]==' ': continue
        print "CHANGED "+s[-1]
        print repr(s[-1])
        \"""
        elif s[0]=='-':
            print(u'Delete "{}" from position {}'.format(s[-1],i))
        elif s[0]=='+':
            print(u'Add "{}" to position {}'.format(s[-1],i))  
        \"""
    """
    s=re.sub(ur'פ\"\S{1,3} דף ',u'',s)
    
    if re.search(ur'[\.,]',s):
        dot_index=re.search(ur'[\.,]',s).start()
        if u'וגו\'' in s[:dot_index]:
            s =u'<b>'+s[:dot_index+1]+u'</b>'+s[dot_index+1:]
    return s
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
def add_cats():
    add_category('Abarbanel', ["Tanakh","Commentary","Abarbanel"],u'אברבנאל')
    add_category('Prophets', ["Tanakh","Commentary","Abarbanel","Prophets"],u'נביאים')
    add_category('Writings', ["Tanakh","Commentary","Abarbanel","Writings"],u'כתובים')

#add_cats()
admin_links=[]
site_links=[]
postme=False
checking=True
if checking:
    with open("Abarbanel_errors.txt", "w") as f:
        f.write("")
for _file in os.listdir("files"):
    if 'txt' in _file and "שופ" not in _file:
        meg = megilah(_file)
        if "Isai" in meg.en_name:
            postme=True
        #if True:#postme:
            #meg.post_ab_index()
            #meg.post_ab_text(True)
            #meg.ab_link() 
            #0/0            
        admin_links.append(SEFARIA_SERVER+"/admin/reset/Abarbanel on "+meg.en_name)
        site_links.append(SEFARIA_SERVER+"/Abarbanel on "+meg.en_name)
for link in admin_links:
    print link
print
for link in site_links:
    print link
        