# -*- coding: utf-8 -*-
import codecs
from sefaria.model import *
from data_utilities import util
from sources import functions
from sources.Scripts import function

footnotes = 'Footnotes on '
footnotes_hebrew = u'\u05d4\u05e2\u05e8\u05d5\u05ea \u05e2\u05dc '

four_dict = function.create_dict('IV', 'Arbah', u'\u05d3', '4', "St.Petersburg, 1883","http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001124682" )
five_dict = function.create_dict('V', 'Chamesh', u'\u05d4', '5', "Vilna, 1885", 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002160720' )
six_dict = function.create_dict('VI', 'Shesh', u'\u05d5', '6', 'Warsaw, 1868', 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001124680')
seven_dict = function.create_dict('VII', 'Sheva', u'\u05d6', '7', 'Warsaw, 1868', 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001124680')

the_dictionaries = {
            '4': four_dict,
            '5': five_dict,
            '6': six_dict,
            '7': seven_dict
        }

def parse_the_text(file_name_teshuvot, file_name_footnotes, dictionary):
    teshuvot_ja = function.parse(file_name_teshuvot)
    footnotes_ja = function.parse(file_name_footnotes)
    links = function.create_links(teshuvot_ja, dictionary)
    index_teshuvot = function.create_index(dictionary)
    index_footnotes = function.create_index(dictionary,footnotes, footnotes_hebrew)
    teshuvot_ja = util.clean_jagged_array(teshuvot_ja, ['\d+', '\+'])
    footnotes_ja = util.clean_jagged_array(footnotes_ja, ['\d+', '\+'])
    text_teshuvot = function.create_text(dictionary, teshuvot_ja)
    text_footnotes = function.create_text(dictionary, footnotes_ja)
    functions.post_index(index_teshuvot)
    functions.post_index(index_footnotes)
    functions.post_text_weak_connection('Teshuvot haRashba part {}'.format(dictionary['roman numeral']), text_teshuvot)
    functions.post_text_weak_connection('Footnotes on Teshuvot haRashba part {}'.format(dictionary['roman numeral']), text_footnotes)
    functions.post_link_weak_connection(links)


for number in range(4,8):
    parse_the_text('rashba{}.txt'.format(str(number)), 'rashba{}cmnt.txt'.format(str(number)), the_dictionaries[str(number)])

# hello = codecs.open("hello.txt", 'w', 'utf-8')
# util.jagged_array_to_file(hello, teshuvot_harashba_4,['Siman', 'Text'])
# hello.close()

