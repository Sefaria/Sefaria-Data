# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *
from Ikkarim_parse_text import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from functions import *
import re
import data_utilities
import codecs
from sources import functions
"""
title_text = ["ספר העקרים","מאת רב יוסף אלבו","הוגה על פי כתבי יד שונים והוצאות עתיקות ונעתק לשפת אנגלית","מאת  יצחק הוזיק","פרופיסור לפילוסופיא באוניורסיטא דפינסילוניא"]

version = {
    'versionTitle': 'Sefer Ha-\'ikkarim',
    'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001187491',
    'language': 'he',
    'text': title_text
}

post_text_weak_connection('Sefer HaIkkarim, Title', version)
"""
print "buidling text..."
Ikkarim_text = get_parsed_text()
"""
print "posting pesicha..."
version = {
    'versionTitle': 'Sefer Ha-\'ikkarim',
    'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001187491',
    'language': 'he',
    'text': Ikkarim_text[0]
}

post_text_weak_connection('Sefer HaIkkarim, Forward', version)

print "posting introduction..."
version = {
    'versionTitle': 'Sefer Ha-\'ikkarim',
    'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001187491',
    'language': 'he',
    'text': Ikkarim_text[1]
    }
    
post_text_weak_connection('Sefer HaIkkarim, Introduction', version)
"""
for index in range(2,3):
    print "posting maamar "+ str(index+1)+" introduction..."
    version = {
        'versionTitle': 'Sefer Ha-\'ikkarim',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001187491',
        'language': 'he',
        'text': Ikkarim_text[2][index][0]
    }
    post_text_weak_connection('Sefer_HaIkkarim,_Maamar_'+str(index+1)+",_Introduction", version)

    print "posting maamar "+ str(index+1)+" body"

    version = {
        'versionTitle': 'Sefer Ha-\'ikkarim',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001187491',
        'language': 'he',
        #maamar 2 has haarah and requires different index
        'text': Ikkarim_text[2][index][1:] if index != 1 else Ikkarim_text[2][index][2:]
    }
    post_text_weak_connection('Sefer_HaIkkarim,_Maamar_'+str(index+1), version)

"""
print "posting maamar 2 haarah..."
version = {
    'versionTitle': 'Sefer Ha-\'ikkarim',
    'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001187491',
    'language': 'he',
    'text': Ikkarim_text[2][1][1]
}
"This is a haarah:"
for p in Ikkarim_text[2][1][1]:
    print p
post_text('Sefer_HaIkkarim,_Maamar_2,_Observation', version,weak_network=True)

"""

