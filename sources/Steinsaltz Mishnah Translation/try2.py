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

def make_mishnah_perek_array(book):
    #hit a bug with Pesach, fixed since then
    tc = TextChunk(Ref(book), "en")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    for index, perek in enumerate(return_array):
        tc = TextChunk(Ref(book+" "+str(index+1)), "en")
        for x in range(len(tc.text)):
            return_array[index].append([])
    return return_array
mishnah_tractate='Berakhot'
ref_array= make_mishnah_perek_array('Mishnah '+mishnah_tractate)
trans_array= make_mishnah_perek_array('Mishnah '+mishnah_tractate)

for pindex, perek in enumerate(ref_array):
    for mindex, mishnah in enumerate(perek):
        longest_ref=None
        for linkdex, link in enumerate(Ref("Mishnah {}, {}.{}".format(mishnah_tractate, pindex+1, mindex+1)).linkset().array()):
            print link.refs
            if Ref(mishnah_tractate).contains(Ref(link.refs[0])):
                text0 = Ref(link.refs[0]).text("he").text
                if not isinstance(text0, basestring):
                    text0=' '.join(text0)                   
                if longest_ref:
                    longest_text=Ref(longest_ref).text('he').text
                    if not isinstance(longest_text, basestring):
                        longest_text=' '.join(longest_text)
                    if len(longest_text)<len(text0):
                        print "{} is longet than {}".format(link.refs[0], longest_ref)
                        longest_ref=link.refs[0]
                    else:
                        print "{} is longet than {}".format(longest_ref,link.refs[0])
                    
                else:
                    longest_ref=link.refs[0]
            if Ref(mishnah_tractate).contains(Ref(link.refs[1])):
                text1 = Ref(link.refs[1]).text("he").text
                if not isinstance(text1,basestring):
                    text1=' '.join(text1)    
                if longest_ref:
                    longest_text=Ref(longest_ref).text('he').text
                    if not isinstance(longest_text, basestring):
                        longest_text=' '.join(longest_text)
                    if len(longest_text)<len(text1):
                        print "{} is longet than {}".format(link.refs[1],longest_ref)
                        longest_ref=link.refs[1]
                    else:
                        print "{} is longet than {}".format(longest_ref,link.refs[1])
                        
                else:
                    longest_ref=link.refs[1]
        print "{} {}:{},LR {}".format(mishnah_tractate, pindex+1, mindex+1,longest_ref)
"""
            if Ref(mishnah_tractate).contains(Ref(link.refs[0])):
                print "FIRST"
                textChunk0 = Ref(link.refs[0]).text("he")                    
                if longest_ref:
                    print ' '.join(Ref(longest_ref).text('he').text)
                    print ' '.join(textChunk0.text)
                    print len(' '.join(Ref(longest_ref).text('he').text).split()),len(' '.join(textChunk0.text).split())
                    
                    if len(' '.join(Ref(longest_ref).text('he').text).split())<len(' '.join(textChunk0.text).split()):

                        print "{} is longet than {}".format(link.refs[0], longest_ref)
                        longest_ref=link.refs[0]
                    else:
                        print "{} is longet than {}".format(longest_ref,link.refs[0])
                    
                else:
                    longest_ref=link.refs[0]

mishnah_links=[]
with open('Mishnah Map.csv', 'rb') as f:
    reader = csv.reader(f)
    for row in reader:
        mishnah_links.append(row)
mishnah_links.pop(0)
current_mesechet=None
for row in mishnah_links:
    print row[0]
    if current_mesechet:
        if current_mesechet!=row[0]:
            print "NEW MESECHET"
            current_mesechet=row[0]
    else:
        current_mesechet=row[0]
"""