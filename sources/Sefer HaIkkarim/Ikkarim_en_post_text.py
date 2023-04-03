# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *
from Ikkarim_en_parse_text import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from functions import *
import re
import linking_utilities
import codecs
from sources import functions

print "buidling text..."
Ikkarim_text = get_parsed_text()
"""
title_text = ["SEFER HA-IKKARIM","BOOK OF PRINCIPLES","BY JOSEPH ALBO","CRITICALLY EDITED ON THE BASIS OF MANUSCRIPTS AND OLD EDITIONS AND PROVIDED WITH A TRANSLATION AND NOTES","BY ISAAC HUSIK, LL.B., M.A., Ph.D.","Professor of Philosophy at the University of Pennsylvania"]
print "posting title..."
version = {
'versionTitle': 'Sefer Ha-ikkarim, Jewish Publication Society of America, 1929',
'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001187491',
'language': 'en',
'text': title_text
}
post_text("Sefer HaIkkarim, Title", version,weak_network=True)

print "posting editors intro..."
version = {
    'versionTitle': 'Sefer Ha-ikkarim, Jewish Publication Society of America, 1929',
    'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001187491',
    'language': 'en',
    'text': Ikkarim_text[0]
}
print Ikkarim_text[0][0]
post_text("Sefer HaIkkarim, Editor's Introduction", version,weak_network=True)

print "posting pesicha..."
version = {
'versionTitle': 'Sefer Ha-ikkarim, Jewish Publication Society of America, 1929',
'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001187491',
'language': 'en',
'text': Ikkarim_text[1]
}
print Ikkarim_text[1][0]

post_text('Sefer HaIkkarim, Forward', version,weak_network=True)

print "posting introduction..."
version = {
'versionTitle': 'Sefer Ha-ikkarim, Jewish Publication Society of America, 1929',
'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001187491',
'language': 'en',
'text': Ikkarim_text[2]
}
print Ikkarim_text[2][0]
post_text('Sefer HaIkkarim, Introduction', version,weak_network=True)
"""
for index in range(0,1):
    
    print "posting maamar "+ str(index+1)+" introduction..."
    version = {
        'versionTitle': 'Sefer Ha-ikkarim, Jewish Publication Society of America, 1929',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001187491',
        'language': 'en',
        'text': Ikkarim_text[3][index][0]
    }
    print Ikkarim_text[3][index][0][0]
    post_text('Sefer_HaIkkarim,_Maamar_'+str(index+1)+",_Introduction", version,weak_network=True)

    print "posting maamar "+ str(index+1)+" body"
    version = {
        'versionTitle': 'Sefer Ha-ikkarim, Jewish Publication Society of America, 1929',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001187491',
        'language': 'en',
        #maamar 2 has haarah and requires different index
        'text':  Ikkarim_text[3][index][1] if index != 1 else Ikkarim_text[3][index][2]
    }
    post_text('Sefer_HaIkkarim,_Maamar_'+str(index+1), version,weak_network=True)

"""
print "posting maamar 2 haarah..."
version = {
    'versionTitle': 'Sefer Ha-ikkarim, Jewish Publication Society of America, 1929',
    'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001187491',
    'language': 'en',
    'text': Ikkarim_text[3][1][1]
}
post_text('Sefer_HaIkkarim,_Maamar_2,_Observation', version, weak_network=True)

"""


