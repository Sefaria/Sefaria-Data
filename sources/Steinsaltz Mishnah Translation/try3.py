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
from fuzzywuzzy import fuzz
import data_utilities
import re
import csv


def get_daf_en(num):
    num-=1
    if num % 2 == 1:
        num = num / 2 + 2
        return str(num)+"a"

    else:
        num = num / 2 + 1
        return str(num)+"b"
def ref_to_chatper(ref,ref_list):
    for index, ch_ref in enumerate(ref_list):
        if Ref(ch_ref).contains(ref):
            return index
def clean_he_line(s):
    s = re.sub(ur'<.*?>',u'',s)
    s.replace(u'מתני׳',u'')
    return s
def make_mishnah_perek_array(book):
    #hit a bug with Pesach, fixed since then
    book = "Mishnah "+book
    tc = TextChunk(Ref(book), "en")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    for index, perek in enumerate(return_array):
        tc = TextChunk(Ref(book+" "+str(index+1)), "en")
        for x in range(len(tc.text)):
            return_array[index].append([u''])
    return return_array
def get_talmud_ref_array(mesechet):
    #print 'making {} ref array...'.format(mesechet)
    in_mishnah=False
    perek_ref_list=[]
    for ch in library.get_index(mesechet).alt_structs['Chapters']['nodes']:
        perek_ref_list.append(ch['wholeRef'])
    line_by_perek=[[] for x in range(len(perek_ref_list))]
    talmud_text=Ref(mesechet).text('he').text
    for daf_num in range(2,len(talmud_text)):
        #for line_num in range(len(Ref('{} {}'.format(mesechet, get_daf_en(daf_num))).text('he').text)):
        for line_num in range(len(talmud_text[daf_num])):
            ref=Ref('{} {}:{}'.format(mesechet, get_daf_en(daf_num),line_num+1))
            line=talmud_text[daf_num][line_num]
            if (u'strong' in line and u'מתני׳' in line) or (line_num==0 and daf_num==2):
                in_mishnah=True
            if u'גמ׳' in line:
                in_mishnah=False
            if in_mishnah:
                line_by_perek[ref_to_chatper(ref, perek_ref_list)].append(ref)
            #if in_mishnah and u':' in line:
            #    in_mishnah=False
    """
    for cindex, chapter in enumerate(line_by_perek):
        for lindex, line in enumerate(chapter):
            print cindex, lindex, line
    """
    return line_by_perek
def post_en_trans(mesechet):
    mishnah_refs=get_talmud_ref_array(mesechet)
    mishnah_text=Ref('Mishnah {}'.format(mesechet)).text('he').text
    en_tran=make_mishnah_perek_array(mesechet)
    
    for pindex, perek in enumerate(mishnah_text):
        perek_ref_counter=0
        for mindex, mishnah in enumerate(perek):
            whats_left=len(mishnah.split())
            trying=True
            while trying and len(mishnah_refs[pindex])>0:
                ref = mishnah_refs[pindex][0]
                ref_text = clean_he_line(ref.text('he').text)
                if len(ref_text.split())/2<=whats_left or mindex==len(perek)-1:
                    whats_left-=len(ref_text.split())
                    mishnah_refs[pindex].pop(0)
                    if len(en_tran[pindex][mindex])<1:
                        en_tran[pindex][mindex]+=ref.text('en').text
                    else:
                        en_tran[pindex][mindex]+=u' '+ref.text('en').text
                else:
                    trying=False
    """
    for pindex, perek in enumerate(en_tran):
        for mindex, mishnah in enumerate(perek):
            print pindex, mindex, u''.join(mishnah)
    """
    final_version=make_mishnah_perek_array(mesechet)
    for pindex, perek in enumerate(en_tran):
        for mindex, mishnah in enumerate(perek):
            final_version[pindex][mindex]= u''.join(mishnah).replace(u'<strong>MISHNA:</strong> ',u'')
    version = {
        'versionTitle': 'William Davidson Edition - English',
        'versionSource': 'www.korenpub.com',
        'language': 'en',
        'text': final_version
    }
    #post_text_weak_connection('Mishnah '+mesechet, version)
    post_text_weak_connection('Mishnah '+mesechet, version)
    
                    
links=[]
for mesechet in library.get_indexes_in_category('Bavli'):
    has_wde=False
    for version in library.get_index(mesechet).versionState().versions('en'):
        if 'William Davidson Edition' in version.versionTitle:
            has_wde=True
    if has_wde: 
        print "posting {}...".format(mesechet)                     
        post_en_trans(mesechet)
        links.append('http://rosh.sandbox.sefaria.org/Mishnah_{}.1?ven=William_Davidson_Edition_-_English&lang=bi'.format(mesechet))
for link in links:
    print link
