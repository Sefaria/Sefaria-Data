# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *
from Shev_Shmatta_parse import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from functions import *
import re
import linking_utilities
import codecs

print "buidling text..."
shev_shmatta_text = get_final_parsed_text()
print "posting introduction..."

for index, shmatta in enumerate(shev_shmatta_text[1:8]):
    print str(index)
    print shmatta[0][0]

#upload introduction
version = {
    'versionTitle': 'Shev Shmatta',
    'versionSource': 'https://he.wikisource.org/wiki/%D7%A9%D7%91_%D7%A9%D7%9E%D7%A2%D7%AA%D7%AA%D7%90',
    'language': 'he',
    'text': shev_shmatta_text[0]
}

post_text_weak_connection('Shev Shmatta, Introduction', version)
"""
#upload body
#for shmatta in enumerate(shev_shmatta_text[7:8]):
for index, shmatta in enumerate(shev_shmatta_text[1:8]):

    version = {
        'versionTitle': 'Shev Shmatta',
        'versionSource': 'https://he.wikisource.org/wiki/%D7%A9%D7%91_%D7%A9%D7%9E%D7%A2%D7%AA%D7%AA%D7%90',
        'language': 'he',
        'text': shmatta
    }

    post_text_weak_connection('Shev Shmatta, Shmatta '+str(index+1), version)


#upload titles
for index, title in enumerate(get_chapter_subjects()):
    version = {
    'versionTitle': 'Shev Shmatta',
    'versionSource': 'https://he.wikisource.org/wiki/%D7%A9%D7%91_%D7%A9%D7%9E%D7%A2%D7%AA%D7%AA%D7%90',
    'language': 'he',
    'text': [title]
    }
    #note that because into doesn't have a title, the indices are one off
    post_text_weak_connection('Shev Shmatta, Shmatta '+str(index+1) +', Subject', version)
"""
