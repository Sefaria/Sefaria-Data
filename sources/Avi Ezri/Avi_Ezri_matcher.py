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
from data_utilities.dibur_hamatchil_matcher import match_ref
import re
import codecs
en_sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
def _filter(some_string):
    if re.search(ur'<b>(.*?)</b>', some_string) is None:
        return False
    else:
        return True

def dh_extract_method(some_string):
    return re.search(ur'<b>(.*?)</b>', some_string).group(1)

def base_tokenizer(some_string):
    return some_string.split()

def get_links(sefer):
    base_ref = TextChunk(Ref(sefer),"he")
    avi_ezri_ref = TextChunk(Ref("Avi Ezri, "+str(sefer_ranges[book_index][1])+"-"+str(sefer_ranges[book_index][2])),"he")
    return match_ref(base_ref,akeida_ref,base_tokenizer,dh_extract_method=dh_extract_method)

for sefer in en_sefer_names:
    links = get_links(sefer)
    for link in links:
        print link

