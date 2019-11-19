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
        self.he_name=file_to_he_name(file_name).decode('utf','replace')
        self.en_name=from_heb_title_to_eng_title(self.he_name)
        self.has_pesicha= self.en_name in has_pesicha
        self.text=[]
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
            intro_node.depth = 1
            intro_node.addressTypes = ['Integer']
            intro_node.sectionNames = ['Paragraph']
            record.append(intro_node)
            
            text_node = JaggedArrayNode()
            text_node.key = "default"
            text_node.default = True
            text_node.depth = 2
            text_node.addressTypes = ['Integer','Integer']
            text_node.sectionNames = ['Parasha','Comment']
            record.append(text_node)
        else:
            record = JaggedArrayNode()
            record.add_title('Etz Yosef on {} Rabbah'.format(self.en_name), 'en', primary=True, )
            record.add_title(u'עץ יוסף על {} רבה'.format(self.he_name), 'he', primary=True, )
            record.key = 'Etz Yosef on {} Rabbah'.format(self.en_name)            
            record.depth = 2
            record.addressTypes = ['Integer','Integer']
            record.sectionNames = ['Parasha','Comment']

        record.validate()

        index = {
            "title":'Etz Yosef on {} Rabbah'.format(self.en_name),
            "base_text_titles": [
               '{} Rabbah'.format(self.en_name)
            ],
            "dependence": "Commentary",
            "categories":['Midrash','Commentary'],
            "schema": record.serialize()
        }
        post_index(index,weak_network=True)
    def parse_ey(self):
        with open('files/'+self.file_name) as tsvfile:
          reader = csv.reader(tsvfile, delimiter='\t')
      
          text_box=[]
          for row in reader:
            if 'פתיחתא' in row[0]:
                in_pesicha=True
            if 'פרשה' in row[0]:
                if len(text_box)>0:
                    if in_pesicha:
                        self.pesicha=text_box
                    else:
                        self.text.append(text_box)
                    text_box=[]
                in_pesicha=False
            text_box.append(row[2])
        self.text.append(text_box)
        """
        if self.has_pesicha:
            for pindex, p in enumerate(self.pesicha):
                print self.en_name, pindex, p
        """
        """
        for paindex, parasha in enumerate(self.text):
            for pindex, paragraph in enumerate(parasha):
                print self.en_name, paindex, pindex, paragraph
        """
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
            
    def make_link_table(self):
        rows=[]
        sample_Ref = Ref("Genesis 1")
        f = open('etz_yoseph_link_table_{}.tsv'.format(self.en_name),'w')
        f.write('Midrash Section\tMidrash Paragraph(from file)\tEY Comment\tMatched Midrash paragraph\n')
        f.close()
        with open('files/'+self.file_name) as tsvfile:
          reader = csv.reader(tsvfile, delimiter='\t')
          text_box=[]
          for row in reader:
              rows.append(row)
        if self.has_pesicha:
            base_chunk = TextChunk(Ref('{} Rabbah, Petichta'.format(self.en_name)),"he")
            com_chunk = TextChunk(Ref('Etz Yosef on {} Rabbah, Petichta'.format(self.en_name)),"he")
            print "linking {} Petichta...".format(self.en_name)
            ch_links = match_ref(base_chunk,com_chunk,base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=_filter)
            with open('etz_yoseph_link_table_{}.tsv'.format(self.en_name),'a') as fd:
                for link_index, (base, comment) in enumerate(zip(ch_links["matches"],ch_links["comment_refs"])):
                    insert_row=rows.pop(0)
                    if base:
                        fd.write('{}\t{}\t{}\t{}\n'.format(insert_row[0],insert_row[1],insert_row[2],base))                        
                    else:
                        fd.write('{}\t{}\t{}\tNULL\n'.format(insert_row[0],insert_row[1],insert_row[2]))                        
                        
                        
        for chapter in range(1,len(TextChunk(Ref('{} Rabbah'.format(self.en_name)),'he').text)+1):
            if True:
                base_chunk = TextChunk(Ref('{} Rabbah, {}'.format(self.en_name,chapter)),"he")
                com_chunk = TextChunk(Ref('Etz Yosef on {} Rabbah, {}'.format(self.en_name, chapter)),"he")
                print "linking {} Parasha {}".format(self.en_name, chapter)
                ch_links = match_ref(base_chunk,com_chunk,base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=_filter)
                
                with open('etz_yoseph_link_table_{}.tsv'.format(self.en_name),'a') as fd:
                    for link_index, (base, comment) in enumerate(zip(ch_links["matches"],ch_links["comment_refs"])):
                        insert_row=rows.pop(0)
                        if base:
                            fd.write('{}\t{}\t{}\t{}\n'.format(insert_row[0],insert_row[1],insert_row[2],base))                        
                        else:
                            fd.write('{}\t{}\t{}\tNULL\n'.format(insert_row[0],insert_row[1],insert_row[2]))
                           

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
def file_to_he_name(file_name):
    return file_name.split('- ')[1].replace('.tsv','')
def from_heb_title_to_eng_title(heb_title):
    for _tuple in (megilos_dict):
        if _tuple[1]==heb_title:
            return _tuple[0]

admin_links=[]
page_links=[]
for ey_file in os.listdir('files'):
    if ".tsv" in ey_file and 'link' not in ey_file:
        ey_meg = Megilah(ey_file)
        ey_meg.post_ey_index()
        ey_meg.parse_ey()  
        #ey_meg.make_link_table()
        admin_links.append("{}/admin/reset/Etz Yosef on {} Rabbah".format(SEFARIA_SERVER, ey_meg.en_name))
        page_links.append("{}/Etz Yosef on {} Rabbah".format(SEFARIA_SERVER, ey_meg.en_name))
for link in admin_links:
    print link
for link in page_links:
    print link 