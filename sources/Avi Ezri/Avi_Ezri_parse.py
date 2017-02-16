# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
import re
import codecs

sefer_names = eng_parshiot = ["Bereishit","Shemot","Vayikra","Bamidbar","Devarim"]
def get_parsed_text():
    #with open('אבי-עזרי.txt') as myfile:
    with open('AE.txt') as myfile:
        text = re.sub(ur"[ \n]{2}","",''.join(list(map(lambda(x): x.decode('utf_8','replace'),myfile.readlines()))))
    #split chapters
    sefer_split = text.split(u"13#1511")[1:]
    for sefer_index, sefer in enumerate(sefer_split):
        chapters = sefer.split("@09")
        sefer_array = make_perek_array(sefer_names[sefer_index])
        for chapter in chapters:
            chapter_index = chapter.split("@73")[0]
            verses = chapter.split("@73")[1].split("@68")
            for verse in verses:
                verse_index = verse.split 
            
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
    
get_parsed_text()