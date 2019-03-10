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
    record = SchemaNode()
    record.add_title('Etz Yosef on Midrash Rabbah', 'en', primary=True, )
    record.add_title(u'עץ יוסף על מדרש רבה', 'he', primary=True, )
    record.key = 'Etz Yosef on Midrash Rabbah'


    for en_sefer, he_sefer in zip(en_sefer_names, he_sefer_names):
        sefer_node = JaggedArrayNode()
        sefer_node.add_title(en_sefer, 'en', primary=True, )
        sefer_node.add_title(he_sefer, 'he', primary=True, )
        sefer_node.key = en_sefer
        sefer_node.depth = 2
        sefer_node.addressTypes = ['Integer', 'Integer']
        sefer_node.sectionNames = ['Chapter','Comment']
        record.append(sefer_node)

    record.validate()

    index = {
        "title":'Etz Yosef on Midrash Rabbah',
        "base_text_titles": [
           "Bereishit Rabbah","Shemot Rabbah","Vayikra Rabbah","Bemidbar Rabbah","Devarim Rabbah"
        ],
        "dependence": "Commentary",
        "categories":['Midrash','Commentary'],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)

def parse_mlt_csvs():
    for index, _file in enumerate(os.listdir("csv_files")):
        if "1" not in _file:
            sefer = en_sefer_names[index]
            sefer_list=[]
            print "parsing", sefer
            with open('csv_files/'+_file, 'rb') as f:
                reader = csv.reader(f)
                box=[]
                for row in reader:
                    if 'פרשה' in row[0] and len(box)>0:
                        sefer_list.append(box)
                        box=[]
                    box.append(row[2])
            sefer_list.append(box)
        
            version = {
                'versionTitle': 'Midrash Rabbah, with Etz Yosef, Warsaw, 1867',
                'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?docid=NNL_ALEPH001987082&context=L&vid=NLI&search_scope=Local&tab=default_tab&lang=iw_IL',
                'language': 'he',
                'text': sefer_list
            }
            #print "Etz Yosef on Midrash Rabbah, {}".format(en_sefer_names[int(re.search(ur'[\d]',file).group())])
            #post_text_weak_connection("Etz Yosef on Midrash Rabbah, {}".format(en_sefer_names[int(re.search(ur'[\d]',file).group())-1]), version)
            post_text("Etz Yosef on Midrash Rabbah, {}".format(sefer),  version,weak_network=True, skip_links=True, index_count="on")
def make_links():
    matched=0.00
    total=0.00
    errored = []
    not_machted = []
    sample_Ref = Ref("Genesis 1")
    for sefer_index, sefer in enumerate(en_sefer_names):
        if "Gen" not in sefer and "Ex" not in sefer and "Lev" not in sefer and "Num" not in sefer:
            if making_link_table:
                f = open('etz_yoseph_link_table_{}.csv'.format(sefer),'w')
                f.write('EY comment, EY current paragraph, Matched MR paragraph\n')
                f.close()
            with open('mismatched_paragraphs_report_{}.txt'.format(en_sefer_names[sefer_index])) as myFile:
                lines = ''.join(myFile.readlines())
            mismatched_chapters = list(map(lambda(x):int(x),lines.replace('\n','').split()))
            
            for chapter in range(1,len(TextChunk(Ref(midrash_names[sefer_index]),'he').text)+1):
                if True:#chapter in mismatched_chapters or not making_link_table:
                    last_not_matched = []

                    last_matched = Ref('{}, {} 1'.format(midrash_names[sefer_index],chapter))
                    base_chunk = TextChunk(Ref('{}, {}'.format(midrash_names[sefer_index],chapter)),"he")
                    com_chunk = TextChunk(Ref('Etz Yosef on Midrash Rabbah, {}:{}'.format(sefer, chapter)),"he")
                    ch_links = match_ref(base_chunk,com_chunk,base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=_filter)
                    print "KEYS:"
                    for key_thing in ch_links.keys():
                        print key_thing
                    print sefer
                    print "BASE ",len(base_chunk.text)
                    print "COM ",len(com_chunk.text)
                    #pdb.set_trace()
                    if 'comment_refs' not in ch_links:
                        print 'NONE for chapter ',chapter
                        continue
                    for link_index, (base, comment) in enumerate(zip(ch_links["matches"],ch_links["comment_refs"])):
                        if base:
                            while len(last_not_matched)>0:
                                print "we had ", last_matched.normal()
                                print "we have ", base.normal()
                                response_set=list(map(lambda(x): int(x),(last_matched.normal().split(':')[-1]+"-"+base.ending_ref().normal_last_section()).split('-')))
                                print "RESPONSE",response_set, "MAX", max(response_set), "MIN", min(response_set)
                                print "so, we'll do ",'{}-{}'.format(min(response_set),max(response_set))
                                first_link='{} {}{}-{}'.format(' '.join(last_matched.normal().split()[:-1]),re.search(ur'\d+:',last_matched.normal()).group(),min(response_set),max(response_set))
                                lnm = last_not_matched.pop(0).normal()
                                link = (
                                        {
                                        "refs": [
                                                 first_link,
                                                 lnm,
                                                 ],
                                        "type": "commentary",
                                        "auto": True,
                                        "generated_by": "sterling_"+key.replace(" ","_")+"_linker"
                                        })
                                if making_link_table:
                                    if "Etz" in lnm:
                                        etz=lnm
                                        mid=first_link
                                    else:
                                        etz=first_link
                                        mid=lnm
                                    with open('etz_yoseph_link_table_{}.csv'.format(sefer),'a') as fd:
                                        if Ref(mid).starting_ref()==Ref(mid).ending_ref():
                                            fd.write('{}, {}\n'.format(TextChunk(Ref(etz),'he').text.encode('utf','replace'), Ref(mid).normal()))
                                        else:
                                            fd.write('{}, \n'.format(TextChunk(Ref(etz),'he').text.encode('utf','replace')))
                                else:
                                    post_link(link, weak_network=True)
                                matched+=1
                            print "B",base,"C", comment
                            if base:
                                link = (
                                        {
                                        "refs": [
                                                 base.normal(),
                                                 comment.normal(),
                                                 ],
                                        "type": "commentary",
                                        "auto": True,
                                        "generated_by": "sterling_"+key.replace(" ","_")+"_linker"
                                        })
                                if making_link_table:
                                    if "Etz" in base.normal():
                                        etz=base.normal()
                                        mid=comment.normal()
                                    else:
                                        etz=comment.normal()
                                        mid=base.normal()
                                    with open('etz_yoseph_link_table_{}.csv'.format(sefer),'a') as fd:
                                        fd.write('{}, {}\n'.format(TextChunk(Ref(etz),'he').text.encode('utf','replace'), mid))
                                else:
                                    post_link(link, weak_network=True)    
                                matched+=1
            

                
                                last_matched=base
               
                        else:
                            #not_machted.append('{}, {} Introduction'.format(key, section["en_title"]))
                            last_not_matched.append(comment.starting_ref())
                            if link_index==len(ch_links["matches"])-1:
                                print "NO LINKS LEFT!"
                                print "we had ", last_matched.normal()
                                print "so, we'll do ",last_matched.normal()+"-"+str(len(base_chunk.text))
                                while len(last_not_matched)>0:
                                    lnm=last_not_matched.pop(0).normal()
                                    first_link=last_matched.normal()+"-"+str(len(base_chunk.text))
                                    link = (
                                            {
                                            "refs": [
                                                     first_link,
                                                     lnm,
                                                     ],
                                            "type": "commentary",
                                            "auto": True,
                                            "generated_by": "sterling_"+key.replace(" ","_")+"_linker"
                                            })
                                    if making_link_table:
                                        if "Etz" in lnm:
                                            etz=lnm
                                            mid=first_link
                                        else:
                                            etz=first_link
                                            mid=lnm
                                        with open('etz_yoseph_link_table_{}.csv'.format(sefer),'a') as fd:
                                            if Ref(mid).starting_ref()==Ref(mid).ending_ref():
                                                fd.write('{}, {}\n'.format(TextChunk(Ref(etz),'he').text.encode('utf','replace'), Ref(mid).normal()))
                                            else:
                                                fd.write('{}, \n'.format(TextChunk(Ref(etz),'he').text.encode('utf','replace')))
                                                
                                    else:
                                        post_link(link, weak_network=True)
                                    matched+=1

    """       
    pm = matched/total
    print "Result is:",matched,total
    print "Percent matched: "+str(pm)
    print "Not Matched:"
    for nm in not_machted:
        print nm
    """
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
def get_parsha_paragraph_index(sef_num):
    with open('csv_files/Etz Yosef - {}.csv'.format(sef_num), 'rb') as f:
        gen_table=get_ignore_table_genesis()
        last_bracket=0
        after_bracket=False
        reader = csv.reader(f)
        para_count=0
        len_list=[]
        for row in reader:
            if len(row[0])>0 and para_count!=0:
                len_list.append(para_count)
                para_count=0
            if len(row[1])>0:
                if sef_num==1:

                    for match in re.findall(ur'\(.*\)', row[1]):
                        #print "TEH LIST", gen_table[len(len_list)]
                        if getGematria(match) in gen_table[len(len_list)] and '[' not in row[1]:
                            print "we skipped ", match
                        elif not after_bracket or getGematria(match)==last_bracket+1:
                            print "we didn't skip", row[1]
                            para_count+=1
                            after_bracket=False
                    for match in re.findall(ur'\[.*\]', row[1]):
                        last_bracket=getGematria(match)
                        after_bracket=True
                else:
                    print "we didn't skip", row[1]
                    para_count+=1
    len_list.append(para_count)
    return len_list
def get_ignore_table_genesis():
    with open('csv_files/Etz Yosef - 1.csv', 'rb') as f:
        reader = csv.reader(f)
        ignores=[]
        ignore_list=[]
        for index, row in enumerate(reader):
            if len(row[0])>0 and index!=0:
                ignore_list.append(ignores)
                ignores=[]
            for match in re.findall(ur'\[.*?\]',row[1]):
                ignores.append(getGematria(match))
    ignore_list.append(ignores)
    for pindex, parsha in enumerate(ignore_list):
        print pindex, parsha
    return ignore_list
def generate_paragraph_report():
    for sefer_index, sefer in enumerate(en_sefer_names):
        #f2 = open('mismatched_paragraphs_report_{}.txt'.format(sefer),'w')
        #tc = TextChunk(Ref('Etz Yosef on Midrash Rabbah, '+sefer), 'he').text
        par_list = get_parsha_paragraph_index(sefer_index+1)
        for x in range(1, len(par_list)+1):      
            if par_list[x-1]!=len(TextChunk(Ref('{}, {}'.format(midrash_names[sefer_index], x)), 'he').text):
                print sefer, x, par_list[x-1], len(TextChunk(Ref('{}, {}'.format(midrash_names[sefer_index], x)), 'he').text)
                #f2.write("{} ".format(x))
        
        #f2.close()
#parse_mlt_csvs()
#get_ignore_table_genesis()
making_link_table=True
make_links()
#generate_paragraph_report()