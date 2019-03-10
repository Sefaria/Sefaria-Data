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
#from fuzzywuzzy import fuzz
en_sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]


def generate_reports():
    for sefer_name in en_sefer_names:
        #with open('{}_base_match.tsv'.format(sefer_name), 'w') as out_file:
        with open("base_match_files/{}_match_result.tsv".format(sefer_name), "w") as record_file:
            lt_text=TextChunk(Ref('Midrash Lekach Tov on Torah, '+sefer_name),'he').text
            for chapter in range(1,len(lt_text)+1):
                if True:#chapter in mismatched_chapters or not making_link_table:
                    last_not_matched = []
                    last_matched = Ref('{}, {}:1'.format(sefer_name,chapter))
                    print '{}, {}'.format(sefer_name, chapter)
                    base_chunk = TextChunk(Ref('{}, {}'.format(sefer_name, chapter)),"he",'Tanach with Text Only')
                    com_chunk = TextChunk(Ref('Midrash Lekach Tov on Torah, {} {}'.format(sefer_name, chapter)),"he")
                    print "THE BASE",base_chunk.text[0]
                    ch_links = match_ref(base_chunk,com_chunk,base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=_filter)
                    print "KEYS:"
                    for key_thing in ch_links.keys():
                        print key_thing
                    print sefer_name
                    print "BASE ",len(base_chunk.text)
                    print "COM ",len(com_chunk.text)
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
                                if "Lek" in lnm:
                                    etz=lnm
                                    mid=first_link
                                else:
                                    etz=first_link
                                    mid=lnm
                                if Ref(mid).starting_ref()==Ref(mid).ending_ref():
                                    record_file.write("{}\t{}\n".format(TextChunk(Ref(etz),'he').text.encode('utf','replace'), Ref(mid).normal()))
                                else:
                                    record_file.write("{}\t\n".format(TextChunk(Ref(etz),'he').text.encode('utf','replace')))
                            print "B",base,"C", comment
                            if "Lek" in base.normal():
                                etz=base.normal()
                                mid=comment.normal()
                            else:
                                etz=comment.normal()
                                mid=base.normal()
                            record_file.write('{}\t{}\n'.format(TextChunk(Ref(etz),'he').text.encode('utf','replace'), Ref(mid).normal()))
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
                                    first_link=last_matched.normal().split('-')[0]+"-"+str(len(base_chunk.text))
                                    if "Lek" in lnm:
                                        etz=lnm
                                        mid=first_link
                                    else:
                                        etz=first_link
                                        mid=lnm
                                    if Ref(mid).starting_ref()==Ref(mid).ending_ref():
                                        record_file.write('{}\t{}\n'.format(TextChunk(Ref(etz),'he').text.encode('utf','replace'), Ref(mid).normal()))
                                    else:
                                        record_file.write('{}\t\n'.format(TextChunk(Ref(etz),'he').text.encode('utf','replace')))
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

generate_reports()
            