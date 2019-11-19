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


megilos_dict=[
    ['Ruth',u'רות'],
    ['Shir HaShirim',u'שיר השירים'],
    ['Eichah',u'איכה'],
    ['Kohelet',u'קהלת'],
    ['Esther',u'אסתר']
]

has_pesicha=['Esther', 'Ruth', 'Eichah']

class Megilah:
    def __init__(self, file_name):
        self.file_name=file_name
        self.en_name=file_to_en_name(file_name).decode('utf','replace')
        self.he_name=from_en_title_to_he_title(self.en_name)
        self.has_pesicha= self.en_name in has_pesicha
        self.three_dim = True if ("Shir" in self.en_name or "Koh" in self.en_name) else False
    def post_ey_index(self):
        if self.has_pesicha:
            record = SchemaNode()
            record.add_title('Etz Yosef on {} Rabbah'.format(self.en_name), 'en', primary=True, )
            record.add_title(u'עץ יוסף על {} רבה'.format(self.he_name), 'he', primary=True, )
            record.key = 'Etz Yosef on {} Rabbah'.format(self.en_name)

            intro_node = JaggedArrayNode()
            intro_node.add_title("Petichta", 'en', primary=True, )
            intro_node.add_title(u'פתיחתא', 'he', primary=True, )
            intro_node.key = "Petichta"
            intro_node.depth = 2
            intro_node.addressTypes = ['Integer','Integer']
            intro_node.sectionNames = ['Paragraph','Comment']
            record.append(intro_node)
            
            text_node = JaggedArrayNode()
            text_node.toc_zoom=2
            text_node.key = "default"
            text_node.default = True
            text_node.depth = 3
            text_node.addressTypes = ['Integer','Integer','Integer']
            text_node.sectionNames = ['Parasha','Paragraph','Comment']
            record.append(text_node)
        else:
            record = JaggedArrayNode()
            record.add_title('Etz Yosef on {} Rabbah'.format(self.en_name), 'en', primary=True, )
            record.add_title(u'עץ יוסף על {} רבה'.format(self.he_name), 'he', primary=True, )
            record.key = 'Etz Yosef on {} Rabbah'.format(self.en_name)
            if self.three_dim:
                record.depth = 4
                record.toc_zoom=3
                record.addressTypes = ['Integer','Integer','Integer',"Integer"]
                record.sectionNames = ['Parasha','Chapter','Midrash','Comment']
            else:            
                record.depth = 3
                record.toc_zoom=2
                record.addressTypes = ['Integer','Integer','Integer']
                record.sectionNames = ['Parasha','Paragraph','Comment']

        record.validate()

        index = {
            "title":'Etz Yosef on {} Rabbah'.format(self.en_name),
            "base_text_titles": [
               '{} Rabbah'.format(self.en_name)
            ],
            "collective_title": "Etz Yosef",
            "dependence": "Commentary",
            "categories":["Midrash","Aggadic Midrash","Midrash Rabbah","Commentary","Etz Yosef"],
            "schema": record.serialize()
        }
        post_index(index,weak_network=True)
    def parse_ey(self):
        with open('edited_files/'+self.file_name) as tsvfile:
          reader = csv.reader(tsvfile, delimiter='\t')
          if self.three_dim:
              text_box=[[[]]]
              past_start=False
              for row in reader:
                if self.en_name in row[3]:
                    past_start=True
                if past_start:
                    ref_pair=row[3].split(' ')[-1].split(':')
                    current_parsha=int(ref_pair[0])
                    current_chapter=int(ref_pair[1])
                    current_midrash=int(ref_pair[2])
                    while len(text_box)<current_parsha:
                        text_box.append([])
                    while len(text_box[-1])<current_chapter:
                        text_box[-1].append([])
                    while len(text_box[-1][-1])<current_midrash:
                        text_box[-1][-1].append([])
                    text_box[current_parsha-1][current_chapter-1][current_midrash-1].append(row[2])
          else:
              text_box=[[]]
              past_start=False
              in_pesicha=not self.has_pesicha
              for row in reader:
                if self.en_name in row[3]:
                    past_start=True
                if past_start:
                    if 'פתיחתא' in row[0]:
                        in_pesicha=True
                    if 'פרשה' in row[0]:
                        if len(text_box)>0:
                            if in_pesicha:
                                self.pesicha=text_box
                                text_box=[[[]]]
                                in_pesicha=False
                    if in_pesicha:
                        while len(text_box)<int(row[3].split(' ')[-1]):
                            text_box.append([])
                        text_box[int(row[3].split(' ')[-1])-1].append(row[2])
                    else:
                        ref_pair=row[3].split(' ')[-1].split(':')
                        current_parsha=int(ref_pair[0])
                        current_paragraph=int(ref_pair[1])
                        while len(text_box)<current_parsha:
                            text_box.append([])
                        while len(text_box[-1])<current_paragraph:
                            text_box[-1].append([])
                        #print row[3]
                        #print current_parsha, current_paragraph
                        text_box[current_parsha-1][current_paragraph-1].append(row[2])
        self.text=text_box
        """
        if self.has_pesicha:
            for pindex, p in enumerate(self.pesicha):
                for cindex, comment in enumerate(p):
                    print "PESICHA",self.en_name, pindex, cindex, comment
        """
        """
        for paindex, parasha in enumerate(self.text):
            for pindex, paragraph in enumerate(parasha):
                for cindex, comment in enumerate(paragraph):
                    print self.en_name, paindex, pindex,cindex, comment
        """
        #0/0
    def post_ey(self):
        if self.has_pesicha:
            version = {
                'versionTitle': 'Midrash Rabbah, with Etz Yosef, Warsaw, 1867',
                'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?docid=NNL_ALEPH001987082&context=L&vid=NLI&search_scope=Local&tab=default_tab&lang=iw_IL',
                'language': 'he',
                'text': self.pesicha
            }
            if 'local' in SEFARIA_SERVER:
                post_text('Etz Yosef on {} Rabbah, Petichta'.format(self.en_name),  version,weak_network=True, skip_links=True, index_count="on")
            else:
                post_text_weak_connection('Etz Yosef on {} Rabbah, Petichta'.format(self.en_name),  version)
                
        version = {
            'versionTitle': 'Midrash Rabbah, with Etz Yosef, Warsaw, 1867',
            'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?docid=NNL_ALEPH001987082&context=L&vid=NLI&search_scope=Local&tab=default_tab&lang=iw_IL',
            'language': 'he',
            'text': self.text
        }
        if 'local' in SEFARIA_SERVER:
            post_text('Etz Yosef on {} Rabbah'.format(self.en_name),  version,weak_network=True, skip_links=True, index_count="on")
        else:
            post_text_weak_connection('Etz Yosef on {} Rabbah'.format(self.en_name),  version)
            
    def post_links(self):
        going=True
        if self.three_dim:
            for parsha_index,parsha in enumerate(self.text):
                for chapter_index, chapter in enumerate(parsha):
                    for midrash_index, midrash in enumerate(chapter):
                        for comment_index, comment in enumerate(midrash):
                            link = (
                                    {
                                    "refs": [
                                             'Etz Yosef on {} Rabbah, {}:{}:{}:{}'.format(self.en_name, parsha_index+1, chapter_index+1,midrash_index+1, comment_index+1),
                                             '{} Rabbah, {}:{}:{}'.format(self.en_name,parsha_index+1, chapter_index+1,midrash_index+1),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_"+self.en_name+"_etzYosef_linker"
                                    })
                            print self.en_name,'def', parsha_index+1
                            post_link(link, weak_network=True)
        else:
            for parsha_index,parsha in enumerate(self.text):
                for paragraph_index, paragraph in enumerate(parsha):
                    for comment_index, comment in enumerate(paragraph):
                        if True:
                            going=False
                            link = (
                                    {
                                    "refs": [
                                             'Etz Yosef on {} Rabbah, {}:{}:{}'.format(self.en_name, parsha_index+1, paragraph_index+1, comment_index+1),
                                             '{} Rabbah, {}:{}'.format(self.en_name,parsha_index+1, paragraph_index+1),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_"+self.en_name+"_etzYosef_linker"
                                    })
                            print self.en_name,'def', parsha_index+1
                            post_link(link, weak_network=True)
            if self.has_pesicha:
                going=True
                for paragraph_index, paragraph in enumerate(self.pesicha):
                    for comment_index, comment in enumerate(paragraph):
                        if True:
                            going=False
                            link = (
                                    {
                                    "refs": [
                                             'Etz Yosef on {} Rabbah, Petichta, {}:{}'.format(self.en_name, paragraph_index+1, comment_index+1),
                                             '{} Rabbah, Petichta, {}'.format(self.en_name, paragraph_index+1),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_"+self.en_name+"_etzYosef_linker"
                                    })
                            print self.en_name,"pes", paragraph_index+1
                            post_link(link, weak_network=True)
        

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
def file_to_en_name(file_name):
    print file_name
    return file_name.split('table_')[1].replace('.tsv','')
def from_en_title_to_he_title(en_title):
    for _tuple in (megilos_dict):
        if _tuple[0]==en_title:
            return _tuple[1]

admin_links=[]
page_links=[]
for ey_file in os.listdir('edited_files'):
    if ".tsv" in ey_file:
        ey_meg = Megilah(ey_file)
        if ey_meg.three_dim:
            ey_meg.post_ey_index()
            ey_meg.parse_ey()
            ey_meg.post_ey()  
            ey_meg.post_links()
            admin_links.append("{}/admin/reset/Etz Yosef on {} Rabbah".format(SEFARIA_SERVER, ey_meg.en_name))
            page_links.append("{}/Etz Yosef on {} Rabbah".format(SEFARIA_SERVER, ey_meg.en_name))
for link in admin_links:
    print link
for link in page_links:
    print link 