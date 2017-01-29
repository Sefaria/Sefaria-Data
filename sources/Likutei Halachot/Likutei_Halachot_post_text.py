# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *
import Likutei_Halachot_parse_text
import Likutei_Halachot_index_post
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
import functions
import re
import data_utilities
import codecs
#from sources import functions
from urllib2 import URLError, HTTPError
from socket import error
import time



print "buidling intro..."
intro_text = Likutei_Halachot_parse_text.get_parsed_intro()
version = {
    'versionTitle': 'Likutei Halachot',
    'versionSource': 'http://www.orhaganuz.co.il',
    'language': 'he',
    'text': intro_text
}
functions.post_text_weak_connection('Likutei Halachot, Author\'s Introduction', version)

print "building body..."

Likutei_Halachot_text = Likutei_Halachot_parse_text.get_parsed_text()
# the get_parsed_text method returns a length-4 array, each entry a length two array where the first item is a list of titles in that order
#and the second item is a list containing the text of each topic, divded as seperate elements in their own arrays.
orders = [ ["Orach Chaim","אורח חיים"],["Yoreh Deah","יורה דעה"],["Even HaEzer","אבן העזר"],["Choshen Mishpat","חושן משפט"]]

for order_index, order_title in enumerate(orders):
    for topic_index, topic_text in enumerate(Likutei_Halachot_text[order_index][1]):
        english_title = Likutei_Halachot_index_post.get_english_title(Likutei_Halachot_text[order_index][0][topic_index], order_title[0])
        #size exceeds mongo limit, so we have to break up each chelek into two sections
        version_number = 1 if topic_index<(len(Likutei_Halachot_text[order_index][1])/2) else 2
        version = {
                'versionTitle': 'Likutei Halachot: '+order_title[0]+' '+str(version_number),
                'versionSource': 'http://www.orhaganuz.co.il',
                'language': 'he',
                'text': topic_text
            }
        print 'Likutei Halachot, '+order_title[0]+', '+english_title+' ',Likutei_Halachot_text[order_index][0][topic_index]
        print topic_text[0][0][0]
        functions.post_text_weak_connection('Likutei Halachot, '+order_title[0]+', '+english_title, version)


