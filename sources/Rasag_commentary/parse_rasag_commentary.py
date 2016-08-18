# -*- coding: utf-8 -*-
import codecs
from sefaria.model import *
import regex
from sources import functions
from data_utilities import util
from sources.Rasag_commentary import rasag_commentary_index_record
from sources.Rasag_commentary import positive_and_negative_parse
from sources.Rasag_commentary import punishments_parse
from sources.Rasag_commentary import rasag_commentaries_functions

"""
index record
parse text
text record
link
clean
"""

# index = rasag_commentary_index_record.create_index()
# functions.post_index(index)


"""
Still need the intro
"""

# positive_mitzvah_number = regex.compile(u'@00\u05e2\u05e9\u05d4((?:\s[\u05d0-\u05ea]{1,4}){1,9})')
# positive_commandments = positive_and_negative_parse.parse('text_positive_commandments.txt', positive_mitzvah_number)


negative_mitzvah_number = regex.compile(u'@00\u05dc[”"]\u05ea((?:\s[\u05d0-\u05ea]{1,4}){1,9})')
negative_commandments = positive_and_negative_parse.parse('text_negative_commandments.txt', negative_mitzvah_number)

# punishments_mitzvah_number = regex.compile(u'@00\u05e2\u05d5\u05e0\u05e9((?:\s[\u05d0-\u05ea]{1,4}.){1,9})')
# punishments = punishments_parse.parse('text_punishments.txt', punishments_mitzvah_number)

# communal_mitzvah_number = regex.compile(u'@00\u05e4\u05e8\u05e9\u05d4((?:\s[\u05d0-\u05ea]{1,4}.){1,9})')
# communal = punishments_parse.parse('text_communal.txt', communal_mitzvah_number)

list_of_links = rasag_commentaries_functions.create_links(negative_commandments)
print list_of_links


"""
Communal
Appendix
Link
"""

util.ja_to_xml(negative_commandments, ['FIRST', 'SECOND', 'THIRD'])