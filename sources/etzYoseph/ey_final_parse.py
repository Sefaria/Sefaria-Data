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
midrash_names= ["Bereishit Rabbah","Shemot Rabbah","Vayikra Rabbah","Bemidbar Rabbah","Devarim Rabbah"]

def post_ey_index():
    # create index record
    for mindex, midrash_name in enumerate(midrash_names):
        if True:#'She' not in midrash_name and "Ber" not in midrash_name:
            record= JaggedArrayNode()
            record.add_title('Etz Yosef on {}'.format(midrash_name), 'en', primary=True, )
            record.add_title(u'עץ יוסף על {} רבה'.format(he_sefer_names[mindex]), 'he', primary=True, )
            record.key = 'Etz Yosef on {}'.format(midrash_name)
            record.depth = 3
            record.addressTypes = ['Integer', 'Integer', 'Integer']
            record.sectionNames = ['Chapter','Paragraph','Comment']
            record.toc_zoom=2
            record.validate()

            index = {
                "title":'Etz Yosef on {}'.format(midrash_name),
                "base_text_titles": [
                   midrash_name
                ],
                "dependence": "Commentary",
                "collective_title":"Etz Yosef",
                "categories":['Midrash','Aggadic Midrash','Midrash Rabbah',"Commentary"],
                "schema": record.serialize()
            }
            post_index(index,weak_network=True)
def post_ey_gen_text():
    file_names=['Etz_Yosef_-_Genesis_-_tags_corrected.csv']
    for index, _file in enumerate(file_names):
        sefer=''
        if 'csv' in _file:
            for name in en_sefer_names:
                if name in _file:
                    sefer=name
            parhsa_list=[]
            chapter_list=[]
            chapter_box=[]
            print "parsing", sefer
            with open('corrected_csvs/'+_file, 'rb') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row[1])>0 and len(chapter_box)>0:
                        chapter_list.append(chapter_box)
                        chapter_box=[]
                    if len(row[0])>0 and len(chapter_list)>0:
                        parhsa_list.append(chapter_list)
                        chapter_list=[]
                    chapter_box.append(row[2])
            chapter_list.append(chapter_box)
            parhsa_list.append(chapter_list)
            
    
            version = {
                'versionTitle': 'Midrash Rabbah, with Etz Yosef, Warsaw, 1867',
                'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?docid=NNL_ALEPH001987082&context=L&vid=NLI&search_scope=Local&tab=default_tab&lang=iw_IL',
                'language': 'he',
                'text': parhsa_list
            }
            post_text("Etz Yosef on {}".format(midrash_names[en_sefer_names.index(sefer)]),  version,weak_network=True, skip_links=True, index_count="on")
def post_other_ey_texts():
    file_names=['Etz_Yoseph_-_Exodus.csv', 'Etz_Yoseph_-_Leviticus.csv', 'Etz_Yoseph_-_Numbers.csv', 'Etz_Yoseph_-_Deuteronomy.csv']
    for _file in file_names:
        for name in en_sefer_names:
            if name in _file:
                sefer=name
        if "De" in sefer:
            with open('corrected_csvs/'+_file, 'rb') as f:
                reader = csv.reader(f)
                final_text=[[[]]]
                current_parsha=0
                current_paragraph=0
                for row in reader:
                    #print row[0], row[1]
                    if "Rab" in row[1]:
                        #print 'pass'
                        current_parsha=int(row[1].split()[2].split(':')[0])
                        current_paragraph=int(row[1].split()[2].split(':')[1])
                        while len(final_text)!=current_parsha:
                            if len(final_text)>current_parsha:
                                print "ERR", sefer, _file
                                print "ERR"
                                print row[0]
                                1/0
                            print len(final_text), current_parsha
                            print "so add parsha"
                            final_text.append([])

                        while len(final_text[-1])!=current_paragraph:
                            if len(final_text[-1])>current_paragraph:
                                print "ERR", sefer, _file
                                print row[0]
                                1/0
                            print len(final_text[-1]), current_paragraph
                            print "so add paragraph"
                            final_text[-1].append([])
                        final_text[-1][-1].append(row[0])
                        print "WE READ", current_parsha, current_paragraph
                        print "We WROTE", len(final_text), len(final_text[-1])
            for pindex, parsha in enumerate(final_text):
                for paindex, paragraph in enumerate(parsha):
                    for cindex, comment in enumerate(paragraph):
                        print sefer, pindex, paindex, cindex, comment
                        
            version = {
                'versionTitle': 'Midrash Rabbah, with Etz Yosef, Warsaw, 1867',
                'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?docid=NNL_ALEPH001987082&context=L&vid=NLI&search_scope=Local&tab=default_tab&lang=iw_IL',
                'language': 'he',
                'text': final_text
            }
            post_text("Etz Yosef on {}".format(midrash_names[en_sefer_names.index(sefer)]),  version,weak_network=True, skip_links=True, index_count="on")
            post_text_weak_connection("Etz Yosef on {}".format(midrash_names[en_sefer_names.index(sefer)]),  version)#,weak_network=True, skip_links=True, index_count="on")
            
def link_midrash():
    for midrash_name in midrash_names:
        if "Bem" in midrash_name or "Dev" in midrash_name or "Ex" in midrash_name:
            for pindex,parsha in enumerate(TextChunk(Ref('Etz Yosef on {}'.format(midrash_name)), 'he').text):
                if pindex>5 or "Dev" in midrash_name or "Ex" in midrash_name:
                    for cindex, chapter in enumerate(parsha):
                        for paindex, paragraph in enumerate(chapter):
                            link = (
                                    {
                                    "refs": [
                                             'Etz Yosef on {}, {}:{}:{}'.format(midrash_name,pindex+1, cindex+1, paindex+1),
                                             '{} {}:{}'.format(midrash_name,pindex+1, cindex+1),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_etz_yoseph_linker"
                                    })
                            print "linked ", midrash_name
                            print pindex
                            post_link(link, weak_network=True)
def post_midrash_comment_cat():
    add_category("Commentary", ["Midrash",'Aggadic Midrash','Midrash Rabbah',"Commentary"],'מפרשים')
#post_midrash_comment_cat()
#post_ey_index()
#post_ey_gen_text()
#post_other_ey_texts()
link_midrash()