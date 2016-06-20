# encoding=utf-8
import re
import codecs
from data_utilities.sanity_checks import TagTester
from data_utilities import util

"""
מקרא:

@44 קישור ואות לינוך.
@66מצב אות רגיל.
@55 ציטוט מודש.
@88 סוגרים.
@30 מצוה.
@29 סוף מצוה.

"""


def check_chapters():
    with codecs.open('Minchat_Chinuch.txt', 'r', 'utf-8') as chinuch:
        test = TagTester(u'@30', chinuch, u'@30מצוה ([\u05d0-\u05ea"]{1,5})')

        index = 1

        for header in test.grab_each_header(capture_group=1):

            header = header.replace(u'"', u'')
            count = util.getGematria(header)

            if count != index:
                print header
                index = count
            index += 1

