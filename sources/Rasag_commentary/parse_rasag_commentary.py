# -*- coding: utf-8 -*-
import codecs
from sefaria.model import *
import regex
from sources import functions
from data_utilities import util
from sources.Rasag_commentary import rasag_commentary_index_record
from sources.Rasag_commentary import positive_and_negative_parse

"""
index record
parse text
text record
link
clean
"""

# index = rasag_commentary_index_record.create_index()
# functions.post_index(index)
#
# rasag_commentary = rasag_commentary_index_record.parse()
#
# for key in rasag_commentary:
#     ref = 'Rasag Commentary,_{}'.format(key)
#     if key == 'Commentary':
#         ref = 'Ralbag Esther'
#     text = rasag_commentary_index_record.create_text(rasag_commentary[key])
#     functions.post_text(ref, text)
#
# list_of_links = rasag_commentary_index_record.create_links(rasag_commentary['Commentary'])
# functions.post_link(list_of_links)
#
# rasag_commetary_ja = [rasag_commentary['Introduction'], rasag_commentary['Commentary'], rasag_commentary['Benefits']]

positive_mitzvah_number = regex.compile(u'@00\u05e2\u05e9\u05d4((?:\s[\u05d0-\u05ea]{1,4}){1,9})')
positive_commandments = positive_and_negative_parse.parse('text_positive_commandments.txt', positive_mitzvah_number)


# negative_mitzvah_number = regex.compile(u'@00\u05dc[”"]\u05ea((?:\s[\u05d0-\u05ea]{1,4}){1,9})')
# negative_commandments = positive_and_negative_parse.parse('text_negative_commandments.txt', negative_mitzvah_number)

util.ja_to_xml(positive_commandments, ['FIRST', 'SECOND'])