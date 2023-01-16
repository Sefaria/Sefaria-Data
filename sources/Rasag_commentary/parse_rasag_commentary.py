# -*- coding: utf-8 -*-
import codecs
from sefaria.model import *
import regex
from sources import functions
from parsing_utilities import util
from sources.Rasag_commentary import rasag_commentary_index_record
from sources.Rasag_commentary import positive_and_negative_parse
from sources.Rasag_commentary import punishments_parse
from sources.Rasag_commentary import rasag_commentaries_functions
from sources.Rasag_commentary import miluim_parse
from sources.Rasag_commentary import book_intro_parse

"""
Refs to upload
Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 1
Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 2
Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 3
Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 4
Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 5
Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 6
Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 7, Introduction
Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 7, Shorashim
Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 8
Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 9
Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 10
Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 11
Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 12
Commentary on Sefer Hamitzvot of Rasag, Positive Commandments
Commentary on Sefer Hamitzvot of Rasag, Negative Commandments
Commentary on Sefer Hamitzvot of Rasag, Laws of the Court, Introduction
Commentary on Sefer Hamitzvot of Rasag, Laws of the Court
Commentary on Sefer Hamitzvot of Rasag, Communal Laws, Introduction
Commentary on Sefer Hamitzvot of Rasag, Communal Laws
Commentary on Sefer Hamitzvot of Rasag, Appendix, Introduction
Commentary on Sefer Hamitzvot of Rasag, Appendix
"""

# index = rasag_commentary_index_record.create_index()
# functions.post_index(index)

introduction = book_intro_parse.parse('text_book_intro.txt')

positive_mitzvah_number = regex.compile(u'@00\u05e2\u05e9\u05d4((?:\s[\u05d0-\u05ea]{1,4}){1,9})')
positive_commandments = positive_and_negative_parse.parse('text_positive_commandments.txt', positive_mitzvah_number)

negative_mitzvah_number = regex.compile(u'@00\u05dc[”"]\u05ea((?:\s[\u05d0-\u05ea]{1,4}){1,9})')
negative_commandments = positive_and_negative_parse.parse('text_negative_commandments.txt', negative_mitzvah_number)

punishments_mitzvah_number = regex.compile(u'@00\u05e2\u05d5\u05e0\u05e9((?:\s[\u05d0-\u05ea]{1,4}.){1,9})')
punishments = punishments_parse.parse('text_punishments.txt', punishments_mitzvah_number)

communal_mitzvah_number = regex.compile(u'@00\u05e4\u05e8\u05e9\u05d4((?:\s[\u05d0-\u05ea]{1,4}.){1,9})')
communal = punishments_parse.parse('text_communal.txt', communal_mitzvah_number)

miluim = miluim_parse.parse('text_appendix.txt')

#
# for number in range(1, 7):
#     ref = 'Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter {}'.format(number)
#     text = rasag_commentaries_functions.create_text(introduction[number-1])
#     functions.post_text(ref, text)
#
# ref = 'Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 7, Introduction'
# text = rasag_commentaries_functions.create_text(introduction[6][0])
# functions.post_text(ref, text)
#
# ref = 'Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter 7, Shorashim'
# text = rasag_commentaries_functions.create_text(introduction[6][1])
# functions.post_text(ref, text)
#
# for number in range(8, 13):
#     ref = 'Commentary on Sefer Hamitzvot of Rasag, Introduction, Chapter {}'.format(number)
#     text = rasag_commentaries_functions.create_text(introduction[number-1])
#     functions.post_text(ref, text)
#
# ref = 'Commentary on Sefer Hamitzvot of Rasag, Positive Commandments'
# text = rasag_commentaries_functions.create_text(positive_commandments)
# functions.post_text(ref, text)
#
# ref = 'Commentary on Sefer Hamitzvot of Rasag, Negative Commandments'
# text = rasag_commentaries_functions.create_text(negative_commandments)
# functions.post_text(ref, text)
#
# ref = 'Commentary on Sefer Hamitzvot of Rasag, Laws of the Courts, Introduction'
# text = rasag_commentaries_functions.create_text(punishments[0])
# functions.post_text(ref, text)
#
# ref = 'Commentary on Sefer Hamitzvot of Rasag, Laws of the Courts'
# text = rasag_commentaries_functions.create_text(punishments[1])
# functions.post_text(ref, text)
#
util.ja_to_xml(communal[1], ['FIRST', 'SECOND', 'THIRD', 'FOURTH', 'FIFTH'])
#
# ref = 'Commentary on Sefer Hamitzvot of Rasag, Communal Laws, Introduction'
# text = rasag_commentaries_functions.create_text(communal[0])
# functions.post_text(ref, text)
#
ref = 'Commentary on Sefer Hamitzvot of Rasag, Communal Laws'
text = rasag_commentaries_functions.create_text(communal[1])
functions.post_text(ref, text)
#
# ref = 'Commentary on Sefer Hamitzvot of Rasag, Appendix, Introduction'
# text = rasag_commentaries_functions.create_text(miluim[0])
# functions.post_text(ref, text)
#
# ref = 'Commentary on Sefer Hamitzvot of Rasag, Appendix'
# text = rasag_commentaries_functions.create_text(miluim[1])
# functions.post_text(ref, text)


"""
Link
"""
# list_of_links_positive = rasag_commentaries_functions.create_links(positive_commandments, 'Positive Commandments')
# print list_of_links_positive
# functions.post_link(list_of_links_positive)
#
# list_of_links_negative = rasag_commentaries_functions.create_links(negative_commandments, 'Negative Commandments')
# print list_of_links_negative
# functions.post_link(list_of_links_negative)
#
# list_of_links_laws = rasag_commentaries_functions.create_links(punishments[1], 'Laws of the Courts')
# print list_of_links_laws
# functions.post_link(list_of_links_laws)
#
# list_of_links_communal = rasag_commentaries_functions.create_links(communal[1], 'Communal Laws')
# print list_of_links_communal
# functions.post_link(list_of_links_communal)



# util.ja_to_xml(communal, ['FIRST', 'SECOND', 'THIRD', 'FOURTH', 'FIFTH'])