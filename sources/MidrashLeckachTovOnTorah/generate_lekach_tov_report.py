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
import csv

def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
"""
lk_files = ['לקח טוב בראשית.txt','לקח טוב שמות.txt','לקח טוב ויקרא.txt','לקח טוב במדבר.txt','לקח טוב דברים.txt']
sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]

sefer_dict = {}

for sefer in sefer_names:
    sefer_dict[sefef]=make_perek_array(sefef)

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
    
def post_lk_text():
    for file in lk_files:
        with open('files/'+file) as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        for line in lines:
            print line


post_lk_text()
"""
def post_index_lt():
    # create index record
    record = SchemaNode()
    record.add_title('Midrash Lekach Tov on Torah', 'en', primary=True, )
    record.add_title(u'מדרש לקח טוב על תורה', 'he', primary=True, )
    record.key = 'Midrash Lekach Tov on Torah'

    en_sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
    he_sefer_names =  [u"בראשית",u"שמות" ,u"ויקרא",u"במדבר",u"דברים"]
    for en_sefer, he_sefer in zip(en_sefer_names, he_sefer_names):
        sefer_node = JaggedArrayNode()
        sefer_node.add_title(en_sefer, 'en', primary=True, )
        sefer_node.add_title(he_sefer, 'he', primary=True, )
        sefer_node.key = en_sefer
        sefer_node.depth = 1
        sefer_node.addressTypes = ['Integer']
        sefer_node.sectionNames = ['Comment']
        record.append(sefer_node)

    record.validate()

    index = {
        "title":"Midrash Lekach Tov on Torah",
        "base_text_titles": [
           "Genesis","Exodus","Leviticus","Numbers","Deuteronomy"
        ],
        "dependence": "Commentary",
        "categories":['Tanakh','Commentary'],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
lk_files = ['לקח טוב ויקרא.txt','לקח טוב במדבר.txt','לקח טוב דברים.txt']
sefer_names = ["Leviticus","Numbers","Deuteronomy"]

def post_lt_texts():
    for findex, file_name in enumerate(lk_files):
        with open('files/'+file_name) as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        past_start=False
        comment_list=[]
        for line in lines:
            if u'@11' in line:
                past_start=True
            if past_start and not_blank(line):
                comment_list.append(line)
        version = {
            'versionTitle': 'Midrash Lekach Tov on Torah, Vilna 1884',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001922206',
            'language': 'he',
            'text': comment_list
        }
        post_text('Midrash Lekach Tov on Torah, '+sefer_names[findex], version,weak_network=True, skip_links=True, index_count="on")
def extract_ref(s, sefer):
    return s.split(sefer)[-1].strip()          
def make_link_report():
    report_sefer_names = ["Leviticus","Numbers","Deuteronomy"]
    #for round 2, corrections...
    report_sefer_names = ["Deuteronomy"]
    
    not_machted = []
    for sefer_index, sefer in enumerate(report_sefer_names):
        f = open('lekach_tov_link_table2_{}.csv'.format(sefer),'w')
        f.write('Lekach Tov Position, Perek+Pasuk\n')
        f.close()
        last_not_matched = []

        last_matched = Ref('{}, 1:1'.format(sefer))
        base_chunk = TextChunk(Ref(sefer),"he",'Tanach with Text Only')
        #print base_chunk.text
        com_chunk = TextChunk(Ref('Midrash Lekach Tov on Torah, '+sefer),"he")
        ch_links = match_ref(base_chunk,com_chunk,base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=_filter)
        #print sefer
        if 'comment_refs' not in ch_links:
            print 'NONE for chapter ',chapter
            continue
        for link_index, (base, comment) in enumerate(zip(ch_links["matches"],ch_links["comment_refs"])):
            print "B",base,"C", comment
            if base:

                while len(last_not_matched)>0:
                    print "we had ", last_matched.normal()
                    print "we have ", base.normal()
                    print "so, we'll do ",'{}-{}'.format(last_matched.normal(),extract_ref(base.normal(), sefer))
                    first_link='{}-{}'.format(last_matched.normal(),extract_ref(base.normal(), sefer))
                    lnm = last_not_matched.pop(0).normal()
                    print "FIRST LINK", first_link
                    with open('lekach_tov_link_table2_{}.csv'.format(sefer),'a') as fd:
                        lk_ref = extract_ref(lnm, sefer)
                        extracted_ref= extract_ref(first_link, sefer)
                        print "EXTRACTED",extracted_ref
                        print "SPLIT",extracted_ref.split('-')[0],extracted_ref.split('-')[1]
                        if extracted_ref.split('-')[0]==extracted_ref.split('-')[1]:
                            print "EQUAL"
                            fd.write('\"{}\", {}\n'.format(from_ref_to_text(sefer,lk_ref),last_matched.normal()))
                        else:
                            print "UNEQUAL"
                            fd.write('\"{}\", \n'.format(from_ref_to_text(sefer,lk_ref)))#extract_ref(first_link, sefer)))
                with open('lekach_tov_link_table2_{}.csv'.format(sefer),'a') as fd:
                    lk_ref=extract_ref(comment.normal(), sefer)
                    fd.write('\"{}\", {}\n'.format(from_ref_to_text(sefer, lk_ref), extract_ref(base.normal(), sefer)))
                last_matched=base
   
            else:
                last_not_matched.append(comment.starting_ref())
                if link_index==len(ch_links["matches"])-1:
                    while len(last_not_matched)>0:
                        lnm=last_not_matched.pop(0).normal()
                        first_link=last_matched.normal()+"-END"
                        lk_ref=extract_ref(lnm, sefer)
                        with open('lekach_tov_link_table2_{}.csv'.format(sefer),'a') as fd:
                            if last_matched.normal() == Ref(sefer).last_segment_ref().normal():
                                fd.write('\"{}\", {}\n'.format(from_ref_to_text(sefer, lk_ref), first_link))
                            else:
                                fd.write('\"{}\", \n'.format(from_ref_to_text(sefer, lk_ref)))#, first_link)
def from_ref_to_text(sefer, lk_ref):
    return_text= TextChunk(Ref('Midrash Lekach Tov on Torah, {} {}'.format(sefer, lk_ref)),"he").text.encode('utf','replace').replace('\n','').replace('"','""')
    print "RETURNING",return_text
    return return_text
def _filter(some_string):
    #if re.search(ur'פס\'\.', some_string) is None:
    if u'@11' not in some_string or u'@22' not in some_string:
        return False
    else:
        return True

def dh_extract_method(some_string):
    #print "DH!:",some_string
    #print "THE DH",re.search(ur'(?<=פס\'\.)[^\.,]*', some_string).group(0).replace(u"@11",u'')
    print "FINDING DH", some_string
    if u'פס\'.' in some_string:
        return re.search(ur'(?<=פס\'\.)[^\.]*', some_string).group(0).replace(u"@11",u'')
    else:
        return re.search(ur'(?<=@11).*?(?=@22)',some_string).group(0)

def base_tokenizer(some_string):
    #print "THE BASE", some_string
    return filter(lambda(x): x!=u'',remove_extra_spaces(some_string).split(" "))
def remove_extra_spaces(string):
    string = re.sub(ur"\. $",u".",string)
    while u"  " in string:
        string=string.replace(u"  ",u" ")
    return string
    
def combine_reports():
    report_sefer_names = ["Numbers","Deuteronomy"]
    original={}
    appended=[]
    for sefer_name in report_sefer_names:
        f = open('lekach_tov_link_table_corrected_{}.csv'.format(sefer_name),'w')
        f.close()
        with open('lekach_tov_link_table_{}.csv'.format(sefer_name), 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                if "Lek" not in row[0]:
                    original[row[0]]=row[1]
        with open('lekach_tov_link_table2_{}.csv'.format(sefer_name), 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                if "Lek" not in row[0]:
                    with open('lekach_tov_link_table_corrected_{}.csv'.format(sefer_name),'a') as fd:
                        if row[0] in original:
                            fd.write('{}, {}\n'.format(row[0], original[row[0]]))
                        else:
                            fd.write('{}, {}\n'.format(row[0], row[1])) 
                        
                    
#post_index_lt()
#post_lt_texts()
#make_link_report()
combine_reports()

    