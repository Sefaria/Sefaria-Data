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
from sources.Rasag_commentary import miluim_parse
from sources.Rasag_commentary import book_intro_parse

"""
Refs to upload
Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 1
Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 2
Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 3
Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 4
Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 5
Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 6
Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 7, Introduction
Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 7
Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 8
Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 9
Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 10
Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 11
Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 12
Rav Perla on Sefer Hamitzvot of Rasag, Positive Commandments
Rav Perla on Sefer Hamitzvot of Rasag, Negative Commandments
Rav Perla on Sefer Hamitzvot of Rasag, Laws of the Court, Introduction
Rav Perla on Sefer Hamitzvot of Rasag, Laws of the Court
Rav Perla on Sefer Hamitzvot of Rasag, Communal Laws, Introduction
Rav Perla on Sefer Hamitzvot of Rasag, Communal Laws
Rav Perla on Sefer Hamitzvot of Rasag, Appendix, Introduction
Rav Perla on Sefer Hamitzvot of Rasag, Appendix
"""

index = rasag_commentary_index_record.create_index()
functions.post_index(index)

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


for number in range(1, 7):
    ref = 'Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter {}'.format(number)
    text = rasag_commentaries_functions.create_text(introduction[number-1])
    functions.post_text(ref, text)

ref = 'Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 7, Introduction'
text = rasag_commentaries_functions.create_text(introduction[6][0])
functions.post_text(ref, text)

ref = 'Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter 7'
text = rasag_commentaries_functions.create_text(introduction[6][1])
functions.post_text(ref, text)

for number in range(8, 13):
    ref = 'Rav Perla on Sefer Hamitzvot of Rasag, Introduction, Chapter {}'.format(number)
    text = rasag_commentaries_functions.create_text(introduction[number-1])
    functions.post_text(ref, text)

ref = 'Rav Perla on Sefer Hamitzvot of Rasag, Positive Commandments'
text = rasag_commentaries_functions.create_text(positive_commandments)
functions.post_text(ref, text)

ref = 'Rav Perla on Sefer Hamitzvot of Rasag, Negative Commandments'
text = rasag_commentaries_functions.create_text(negative_commandments)
functions.post_text(ref, text)

ref = 'Rav Perla on Sefer Hamitzvot of Rasag, Laws of the Court, Introduction'
text = rasag_commentaries_functions.create_text(punishments[0])
functions.post_text(ref, text)

ref = 'Rav Perla on Sefer Hamitzvot of Rasag, Laws of the Court'
text = rasag_commentaries_functions.create_text(punishments[1])
functions.post_text(ref, text)

ref = 'Rav Perla on Sefer Hamitzvot of Rasag, Communal Laws, Introduction'
text = rasag_commentaries_functions.create_text(communal[0])
functions.post_text(ref, text)

ref = 'Rav Perla on Sefer Hamitzvot of Rasag, Communal Laws'
text = rasag_commentaries_functions.create_text(communal[1])
functions.post_text(ref, text)

ref = 'Rav Perla on Sefer Hamitzvot of Rasag, Appendix, Introduction'
text = rasag_commentaries_functions.create_text(miluim[0])
functions.post_text(ref, text)

ref = 'Rav Perla on Sefer Hamitzvot of Rasag, Appendix'
text = rasag_commentaries_functions.create_text(miluim[1])
functions.post_text(ref, text)


"""
Link
"""
# list_of_links = rasag_commentaries_functions.create_links(negative_commandments)
# print list_of_links



#util.ja_to_xml(introduction, ['FIRST', 'SECOND', 'THIRD', 'FOURTH', 'FIFTH'])