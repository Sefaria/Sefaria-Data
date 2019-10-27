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
import csv


comment_dict={
    'Peirush':u'פירוש',
    'Tosafot':u'תוספות'
}
go_back_list=[u'רמז',u'פירוש',u'דרש',u'סוד']
def not_blank(s):
    if isinstance(s, unicode):
        while u" " in s:
            s = s.replace(u" ",u"")
        return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);
def is_going_back(ref):
    for back_phrase in go_back_list:
        if re.search(ur'^(<b>)?{}'.format(back_phrase),TextChunk(ref,'he').text):
            return True
    return False
class Commentary:
    def __init__(self,file_name_):
        self.file_name=file_name_
        self.he_commentary_name=u'פירוש' if 'פירוש' in file_name_ else u'תוספות'
        for key in comment_dict.keys():
            if self.he_commentary_name in comment_dict[key]:
                self.en_commentary_name=key
    def post_kr_index(self):
        record = JaggedArrayNode()
        record.add_title('Kisse Rachamim {} on Avot D\'Rabbi Natan'.format(self.en_commentary_name), 'en', primary=True, )
        record.add_title(u'כסע רחמים {} על אבות דרבי נתן'.format(self.he_commentary_name), 'he', primary=True, )
        record.key = 'Kisse Rachamim {} on Avot D\'Rabbi Natan'.format(self.en_commentary_name)       
        record.depth = 2
        record.addressTypes = ['Integer','Integer']
        record.sectionNames = ['Chapter','Comment']

        record.validate()

        index = {
            "title":'Kisse Rachamim {} on Avot D\'Rabbi Natan'.format(self.en_commentary_name),
            "base_text_titles": [
               'Avot D\'Rabbi Natan'
            ],
            "dependence": "Commentary",
            "categories":['Midrash','Commentary'],
            "schema": record.serialize()
        }
        post_index(index,weak_network=True)
    def parse_text(self):
        with open('files/'+kr_file) as tsvfile:
          reader = csv.reader(tsvfile)
          text_box=[[] for x in range(41)]
          for row in reader:
              if not_blank(row[1]):
                  text_box[int(re.search(ur'\S+$',row[0]).group())-1].append(row[1])
        if "Pei" in self.en_commentary_name:
            real_chapter_3=text_box[1][50:]
            text_box[1]=text_box[1][:50]
            text_box.insert(2,real_chapter_3)
            
        """
        for cindex, chapter in enumerate(text_box):
            for coindex, comment in enumerate(chapter):
                print self.en_commentary_name, cindex, coindex, comment
        """
        version = {
            'versionTitle': 'Kisse Rahamim, Livorno, 1803',
            'versionSource': 'SOURCE',
            'language': 'he',
            'text': text_box
        }
        print "posting "+self.en_commentary_name+" text..."
        if 'local' in SEFARIA_SERVER:
            post_text('Kisse Rachamim {} on Avot D\'Rabbi Natan'.format(self.en_commentary_name),  version,weak_network=True, skip_links=True, index_count="on")
        else:
            post_text_weak_connection('Kisse Rachamim {} on Avot D\'Rabbi Natan'.format(self.en_commentary_name),  version)
    def make_links(self):
        all_indices=[]
        for cindex, chapter in enumerate(TextChunk(Ref('Avot D\'Rabbi Natan'),"he").text):
            for hindex, halacha in enumerate(chapter):
                all_indices.append('Avot D\'Rabbi Natan {}:{}'.format(cindex+1, hindex+1))
        with open('KisseRachamim_{}_links.tsv'.format(self.en_commentary_name),'w') as record_file:
            print "linking...",self.en_commentary_name
            for chapter in range(1,42):
                print "Chapter {}...".format(chapter)
                not_matched = []
                last_matched=None
                com_chunk=TextChunk(Ref('Kisse Rachamim {} on Avot D\'Rabbi Natan {}'.format(self.en_commentary_name, chapter)),'he')
                base_chunk = TextChunk(Ref('Avot D\'Rabbi Natan {}'.format(chapter)),"he")
                ch_links = match_ref(base_chunk,com_chunk,base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=_filter)
                if "comment_refs" in ch_links:
                    for link_index, (base, comment) in enumerate(zip(ch_links["matches"],ch_links["comment_refs"])):
                        if base:
                            if base==last_matched:
                                while len(not_matched)>0:
                                    adding=not_matched.pop(0)
                                    record_file.write('{}\t{}\t{}\n'.format(adding.normal(),TextChunk(adding,'he').text.replace(u'\n',u'').encode('utf','replace'), base.normal()))
                            else:
                                while len(not_matched)>0:
                                    adding=not_matched.pop(0)
                                    record_file.write('{}\t{}\tNULL\n'.format(adding.normal(),TextChunk(adding,'he').text.replace(u'\n',u'').encode('utf','replace')))
                                    
                            if "Pei" in self.en_commentary_name:
                                if base.normal() in all_indices:
                                    all_indices.remove(base.normal())

                            last_matched=base
                            
                            record_file.write('{}\t{}\t{}\n'.format(comment.normal(),TextChunk(comment,'he').text.replace(u'\n',u'').encode('utf','replace'), base.normal()))
                        else:
                            if is_going_back(comment) and len(not_matched)<1 and last_matched:
                                record_file.write('{}\t{}\t{}\n'.format(comment.normal(),TextChunk(comment,'he').text.replace(u'\n',u'').encode('utf','replace'), last_matched.normal()))
                            else:
                                not_matched.append(comment)
                                
                while len(not_matched)>0:
                    adding=not_matched.pop(0)
                    record_file.write('{}\t{}\tNULL\n'.format(adding.normal(),TextChunk(adding,'he').text.replace(u'\n',u'').encode('utf','replace')))
        if "Pei" in self.en_commentary_name:
            print "These are missing:"
            for index in all_indices:
                print index
    
def _filter(some_string):
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
    

admin_links=[]
page_links=[]        
for kr_file in os.listdir('files'):
    if 'csv' in kr_file and 'פיר' not in kr_file:
        kr_object=Commentary(kr_file)
        #kr_object.post_kr_index()
        #kr_object.parse_text()
        kr_object.make_links()
        admin_links.append("{}/admin/reset/Kisse Rachamim {} on Avot D\'Rabbi Natan".format(SEFARIA_SERVER, kr_object.en_commentary_name))
        page_links.append("{}/Kisse Rachamim {} on Avot D\'Rabbi Natan".format(SEFARIA_SERVER, kr_object.en_commentary_name))
for link in admin_links:
    print link
print
print
for link in page_links:
    print link
