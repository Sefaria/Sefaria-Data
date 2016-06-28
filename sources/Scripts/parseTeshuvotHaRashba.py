# -*- coding: utf-8 -*-
import codecs
from sources.Scripts import parseRashba7
from sources import functions
from sources.Scripts import function
from data_utilities import util


footnotes = 'Footnotes on '
footnotes_hebrew = u'\u05d4\u05e2\u05e8\u05d5\u05ea \u05e2\u05dc '



four_dict = function.create_dict('IV', 'Arbah', u'\u05d3', '4', "St.Petersburg, 1883","http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001124682" )
five_dict = function.create_dict('V', 'Chamesh', u'\u05d4', '5', "Vilna, 1885", 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002160720' )
six_dict = function.create_dict('VI', 'Shesh', u'\u05d5', '6', 'Warsaw, 1868', 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001124680')
seven_dict = function.create_dict('VII', 'Sheva', u'\u05d6', '7', 'Warsaw, 1868', 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001124680')

teshuvot_harashba_4 = function.parse('rashba4.txt')
teshuvot_harashba_5 = function.parse('rashba5.txt')
teshuvot_harashba_6 = function.parse('rashba6.txt')
teshuvot_harashba_7 = function.parse('rashba7.txt')
teshuvot_harashba_footnotes_4 = function.parse('rashba4cmnt.txt')
teshuvot_harashba_footnotes_5 = function.parse('rashba5cmnt.txt')
teshuvot_harashba_footnotes_6 = function.parse('rashba6cmnt.txt')
teshuvot_harashba_footnotes_7 = function.parse('rashba7cmnt.txt')

list_of_links_4 = function.create_links(teshuvot_harashba_4, 'IV')
list_of_links_5 = function.create_links(teshuvot_harashba_5, 'V')
list_of_links_6 = function.create_links(teshuvot_harashba_6, 'VI')
list_of_links_7 = function.create_links(teshuvot_harashba_7, 'VII')

teshuvot_harashba_index_4 = function.create_index(four_dict)
teshuvot_harashba_index_5 = function.create_index(five_dict)
teshuvot_harashba_index_6 = function.create_index(six_dict)
teshuvot_harashba_index_7 = function.create_index(seven_dict)
teshuvot_harashba_footnotes_index_4 = function.create_index(four_dict, footnotes, footnotes_hebrew)
teshuvot_harashba_footnotes_index_5 = function.create_index(five_dict, footnotes, footnotes_hebrew)
teshuvot_harashba_footnotes_index_6 = function.create_index(six_dict, footnotes, footnotes_hebrew)
teshuvot_harashba_footnotes_index_7 = function.create_index(seven_dict, footnotes, footnotes_hebrew)








teshuvot_harashba_text_4 = function.create_text(four_dict, '')
teshuvot_harashba_text_5 = function.create_text(five_dict, '')
teshuvot_harashba_text_6 = function.create_text(six_dict, '')
teshuvot_harashba_text_7 = function.create_text(seven_dict, '')
teshuvot_harashba_footnotes_text_4 = function.create_text(four_dict, '')
teshuvot_harashba_footnotes_text_5 = function.create_text(four_dict, '')
teshuvot_harashba_footnotes_text_6 = function.create_text(four_dict, '')
teshuvot_harashba_footnotes_text_7 = function.create_text(four_dict, '')



#
# hello = codecs.open("hello.txt", 'w', 'utf-8')
# util.jagged_array_to_file(hello, teshuvot_harashba_4,['Siman', 'Text'])
# hello.close()

#
# def post_the_links(list_of_links):
#     for link in list_of_links:
#         functions.post_link(link)
#
#