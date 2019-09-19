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
def not_blank(s):
    if isinstance(s, unicode):
        while u" " in s:
            s = s.replace(u" ",u"")
        return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);
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
            real_chapter_3=[text_box[1][50:]]
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
        with open('KisseRachamim_{}_links.tsv'.format(self.en_commentary_name),'w') as record_file:
            print "linking...",self.en_commentary_name
            for chapter in range(1,42):
                com_chunk=TextChunk(Ref('Kisse Rachamim {} on Avot D\'Rabbi Natan {}'.format(self.en_commentary_name, chapter)),'he')
                base_chunk = TextChunk(Ref('Avot D\'Rabbi Natan {}'.format(chapter)),"he")
                ch_links = match_ref(base_chunk,com_chunk,base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=_filter)
                if "comment_refs" in ch_links:
                    for link_index, (base, comment) in enumerate(zip(ch_links["matches"],ch_links["comment_refs"])):
                        if base:
                            print "B",base,"C", comment
                            if "Kis" in base.normal():
                                ty=base.normal()
                                pasuk=comment.normal()
                            else:
                                ty=comment.normal()
                                pasuk=base.normal()
                            record_file.write('{}\t{}\t{}\n'.format(ty,TextChunk(Ref(ty),'he').text.replace(u'\n',u'').encode('utf','replace'), Ref(pasuk).normal()))
                            last_matched=base
                        else:
                            record_file.write('{}\t{}\tNULL\n'.format(comment.normal(),TextChunk(Ref(comment.normal()),'he').text.replace(u'\n',u'').encode('utf','replace')))

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
    if 'csv' in kr_file and 'פיר' in kr_file:
        kr_object=Commentary(kr_file)
        kr_object.post_kr_index()
        kr_object.parse_text()
        #kr_object.make_links()
        admin_links.append("{}/admin/reset/Kisse Rachamim {} on Avot D\'Rabbi Natan".format(SEFARIA_SERVER, kr_object.en_commentary_name))
        page_links.append("{}/Kisse Rachamim {} on Avot D\'Rabbi Natan".format(SEFARIA_SERVER, kr_object.en_commentary_name))
for link in admin_links:
    print link
print
print
for link in page_links:
    print link
