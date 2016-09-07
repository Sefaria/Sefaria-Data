# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *
from Likutei_Halachot_parse_text import *
from Likutei_Halachot_index_post import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from functions import *
import re
import data_utilities
import codecs
from sources import functions

SEFARIA_SERVER = "http://httpbin.org/post"
print "buidling intro..."
intro_text = get_parsed_intro()
for index, p in enumerate(intro_text):
    print str(index) + " "+p
version = {
    'versionTitle': 'Likutei Halachot',
    'versionSource': 'http://www.orhaganuz.co.il',
    'language': 'he',
    'text': intro_text
}

post_text('Likutei Halachot, Author\'s Introduction', version)

print "building body..."

Likutei_Halachot_text = get_parsed_text()
# the get_parsed_text method returns a length-4 array, each entry a length two array where the first item is a list of titles in that order
#and the second item is a list containing the text of each topic, divded as seperate elements in their own arrays.
orders = [ ["Orach Chaim","אורח חיים"],["Yoreh Deah","יורה דעה"],["Even HaEzer","אבן העזר"],["Choshen Mishpat","חושן משפט"]]

for order_index, order_title in enumerate(orders):
    for topic_index, topic_text in enumerate(Likutei_Halachot_text[order_index][1]):
        english_title = get_english_title(Likutei_Halachot_text[order_index][0][topic_index], order_title[0])
        #size exceeds mongo limit, so we have to break up each chelek into two sections
        version_number = 1 if topic_index<(len(Likutei_Halachot_text[order_index][1])/2) else 2
        print version_number
        version = {
            'versionTitle': 'Likutei Halachot: '+order_title[0]+' '+str(version_number),
            'versionSource': 'http://www.orhaganuz.co.il',
            'language': 'he',
            'text': topic_text[:1][:1][:5]
        }
        print 'Likutei Halachot, '+order_title[0]+', '+english_title
        print topic_text[0][0][0]
        r=post_text('Likutei Halachot, '+order_title[0]+', '+english_title, version)
        print r
#7:10
#12:19
