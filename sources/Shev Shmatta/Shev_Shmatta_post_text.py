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
import data_utilities
import codecs
from sources import functions

print "buidling text..."
shev_shmatta_text = get_final_parsed_text()


#upload introduction
version = {
    'versionTitle': 'Shev Shmatta',
    'versionSource': 'https://he.wikisource.org/',
    'language': 'he',
    'text': shev_shmatta_text[0]
}

post_text('Shev Shmatta, Introduction', version)

#upload body
for index, shmatta in enumerate(shev_shmatta_text[1:8]):
    version = {
    'versionTitle': 'Shev Shmatta',
    'versionSource': 'https://he.wikisource.org/',
    'language': 'he',
    'text': shmatta
    }

    post_text('Shev Shmatta, Shmatta '+str(index+1), version)

#upload titles
for index, title in enumerate(get_chapter_subjects()):
    version = {
    'versionTitle': 'Shev Shmatta',
    'versionSource': 'https://he.wikisource.org/',
    'language': 'he',
    'text': [title]
    }
    #note that because into doesn't have a title, the indices are one off
    post_text('Shev Shmatta, Shmatta '+str(index+1) +', Subject', version)