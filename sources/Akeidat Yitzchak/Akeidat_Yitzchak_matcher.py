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

sefer_ranges=[["Genesis",1,33], ["Exodus",34,56], ["Leviticus",57,71], ["Numbers",72,86], ["Deuteronomy",87,105] ]
def _filter(some_string):
    if re.search(ur'<b>(.*?)</b>', some_string) is None:
        return False
    else:
        return True

def dh_extract_method(some_string):
    print "This is the type:"
    print type(some_string)
    return re.search(ur'<b>(.*?)</b>', some_string).group(1)

def base_tokenizer(some_string):
    return some_string.split()

def get_links(book_index):
    base_ref = TextChunk(Ref(sefer_ranges[book_index][0]),"he")
    akeida_ref = TextChunk(Ref("Akeidat Yitzchak, "+str(sefer_ranges[book_index][1])+"-"+str(sefer_ranges[book_index][2])),"he")
    return match_ref(base_ref,akeida_ref,base_tokenizer,dh_extract_method=dh_extract_method)

for x in range(0,5):
    links = get_links(x)
    for link in links:
        print link

