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
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
def tokenizer(s):
    return s.split()
def get_score(a, b):
    return (len(a) + len(b))/2  # average length of match
pm = ParallelMatcher(tokenizer, all_to_all=False, min_distance_between_matches=1, calculate_score=get_score)

"""
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
        for link in Ref("Mishnah {}, {}.{}".format(mishnah_tractate, pindex+1, mindex+1)).linkset().array():
            if Ref(mishnah_tractate).contains(Ref(link.refs[0])):
                textChunk1 = Ref(link.refs[0]).text("he")    
                textChunk2 = Ref("Mishnah {}, {}.{}".format(mishnah_tractate, pindex+1, mindex+1)).text("he")
                print ' '.join(textChunk1.text)
                print textChunk2.text
                matches = pm.match(tc_list=[textChunk1, textChunk2], return_obj=True)
                matches.sort(key=lambda x: x.score)
                if len(matches)>0:
                    print "THIS IS ME",matches[-1]  # that's the longest match
            if Ref(mishnah_tractate).contains(Ref(link.refs[1])) and link.refs[0]=="Mishnah {} {}:{}".format(mishnah_tractate, pindex+1, mindex+1):
                textChunk1 = Ref(link.refs[1]).text("he")
                textChunk2 = Ref("Mishnah {}, {}.{}".format(mishnah_tractate, pindex+1, mindex+1)).text("he")
                print "G REF",link.refs[1]
                print "M REF","Mishnah {}, {}.{}".format(mishnah_tractate, pindex+1, mindex+1)
                print ' '.join(textChunk1.text)
                print textChunk2.text
                matches = pm.match(tc_list=[textChunk1, textChunk2], return_obj=True)
                print "LENY",len(matches)
                matches.sort(key=lambda x: x.score)
                if len(matches)>0:
                    print "THIS IS ME",matches[-1]  # that's the longest match
                    

for pindex, perek in enumerate(ref_array):
    for mindex, mishnah in enumerate(perek):
        for link in Ref("Mishna {}, {}.{}".format(mishnah_tractate, pindex+1, mindex+1)).linkset().array():
            if Ref(mishnah_tractate).contains(Ref(link.refs[0])):
                #print link.refs[0]
                if "MISHNA" in Ref(link.refs[0].split('-')[0]).text().text:
                    for x in range(0,int(link.refs[0].split('-')[1])-int(link.refs[0].split('-')[0].split()[-1])):
                        if TextChunk(Ref(link.refs[0].split('-')[0]+"-{}".format(int(link.refs[0].split('-')[0].split()[-1]))+x), "he").word_count()>Ref("Mishna {}, {}.{}".format(mishnah_tractate, pindex+1, mindex+1)).text('he').word_count():
                            print link.refs[0].split('-')[0]+"-{}".format(int(link.refs[0].split('-')[0].split()[-1]))+x
                            break
                    #print mindex, pindex, Ref(link.refs[0].split('-')[0]).text().text
                    #print Ref("Mishna {}, {}.{}".format(mishnah_tractate, pindex+1, mindex+1)).text('he').text
                    
            if Ref(mishnah_tractate).contains(Ref(link.refs[1])):
                #print link.refs[1]
                if "MISHNA" in Ref(link.refs[1].split('-')[0]).text().text:
                    for x in range(0,int(link.refs[1].split('-')[1])-int(link.refs[1].split('-')[0].split()[-1].split(":")[1])):
                        print "REF",Ref(link.refs[1].split('-')[0]+"-{}".format(int(link.refs[1].split('-')[0].split()[-1].split(":")[1])+x))
                        print "WC",TextChunk(Ref(link.refs[1].split('-')[0]+"-{}".format(int(link.refs[1].split('-')[0].split()[-1].split(":")[1])+x)),'he').word_count()
                        print "CMR", Ref("Mishna {}, {}.{}".format(mishnah_tractate, pindex+1, mindex+1)).text('he').word_count()
                        if TextChunk(Ref(link.refs[1].split('-')[0]+"-{}".format(int(link.refs[1].split('-')[0].split()[-1].split(":")[1])+x)), "he").word_count()>Ref("Mishna {}, {}.{}".format(mishnah_tractate, pindex+1, mindex+1)).text('he').word_count():
                            print "EURIKA"
                            print link.refs[1].split('-')[0]+"-{}".format(int(link.refs[1].split('-')[0].split()[-1]))+x
                            break
                    print mindex, pindex, Ref(link.refs[1].split('-')[0]).text().text
                    #print Ref("Mishna {}, {}.{}".format(mishnah_tractate, pindex+1, mindex+1)).text('he').text
"""                   
def tokenizer(s):
    return s.split()
def get_score(a, b):
    return (len(a) + len(b))/2  # average length of match
pm = ParallelMatcher(tokenizer, all_to_all=False, min_distance_between_matches=1, calculate_score=get_score)
textChunk1 = Ref("Berakhot 9b:9-10").text("he")
textChunk2 = Ref("Mishnah Berakhot 1:2").text("he")
matches = pm.match(tc_list=[textChunk1, textChunk2], return_obj=True)
matches.sort(key=lambda x: x.score)
print matches[-1]  # that's the longest match
