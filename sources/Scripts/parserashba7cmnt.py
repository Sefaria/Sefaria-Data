# -*- coding: utf-8 -*-
import codecs
from sources.Scripts import parseRashba7
from sources import functions
from data_utilities import util






# list_of_parsed_rashbas = []
# a = [4, 5, 6, 7]
#
# for i in a:
#     rashba_footnote_file = "rashba{}cmnt.txt".format(i)
#     list_of_parsed_rashbas.append(parseRashba7.parse(rashba_footnote_file))
#
#
# for a in list_of_parsed_rashbas:


four_dict = {
    'roman numeral': 'IV',
    'transliterated': 'Arbah',
    'hebrew letter': u'\u05d3',
    'number': '4',
    'version title': "St.Petersburg, 1883",
    'version source': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001124682"
}
five_dict = {
    'roman numeral': 'V',
    'transliterated': 'Chamesh',
    'hebrew letter': u'\u05d4',
    'number': '5',
    'version title': "Vilna, 1885",
    'version source': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002160720'
}
six_dict = {
    'roman numeral': 'VI',
    'transliterated': 'Shesh',
    'hebrew letter': u'\u05d5',
    'number': '6',
    'version title': 'Warsaw, 1868',
    'version source': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001124680'
}
seven_dict = {
    'roman numeral': 'VII',
    'transliterated': 'Sheva',
    'hebrew letter': u'\u05d6',
    'number': '7',
    'version title': 'Warsaw, 1868',
    'version source': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001124680'
}


def post_index_and_text(rashba_footnote, dictionary):
    index = create_index(dictionary['roman numeral'], dictionary['hebrew letter'], dictionary['tranliterated hebrew number'], dictionary['number'])
    text = create_text(dictionary['version title'], dictionary['version source'])
    functions.post_index(index)
    functions.post_text('Footnotes on Teshuvot haRashba part {}'.format(dictionary['roman numeral']), rashba_footnote)
    list_of_links = create_links(rashba_footnote, dictionary['roman numeral'])
    post_the_links(list_of_links)








def create_index(roman_numeral, hebrew_letter, tranliterated_hebrew_number, number):
    return {
        "pubDate": "1470",
        "title": "Footnotes on Teshuvot haRashba part {}".format(roman_numeral),
        "pubPlace": "Rome",
        "maps": [ ],
        "era": "RI",
        "authors": [
            "Rashba"
        ],
        "categories": [
            "Responsa",
            "Rashba"
        ],
        "schema": {
            "nodeType": "JaggedArrayNode",
            "addressTypes": [
                "Integer",
                "Integer"
            ],
            "depth": 2,
            "titles": [
            {
                "lang": "en",
                "text": "Footnotes on Teshuvot helek {}".format(tranliterated_hebrew_number)
            },
            {
                "lang": "en",
                "text": "Footnotes on shut harashba part {}".format(number)
            },
            {
                "lang": "he",
                "text": u"\u05d4\u05e2\u05e8\u05d5\u05ea \u05e2\u05dc \u05e9\u05d5\u0022\u05ea \u05d4\u05e8\u05e9\u05d1\u0022\u05d0 \u05d7\u05dc\u05e7 {}".format(hebrew_letter),
                "primary": True
            },
            {
                "lang": "he",
                "text": u"\u05d4\u05e2\u05e8\u05d5\u05ea \u05e2\u05dc \u05e9\u05d0\u05dc\u05d5\u05ea \u05d5\u05ea\u05e9\u05d5\u05d1\u05d5\u05ea \u05d4\u05e8\u05e9\u05d1\u0022\u05d0 \u05d7\u05dc\u05e7 {}".format(hebrew_letter)
            },
            {
                "lang": "he",
                "text": u"\u05d4\u05e2\u05e8\u05d5\u05ea \u05e2\u05dc \u05e9\u05d5\u0022\u05ea \u05d4\u05e8\u05e9\u05d1\u0022\u05d0 {}".format(hebrew_letter)
            },
            {
                "lang": "en",
                "text": "Footnotes on Teshuvot haRashba part {}".format(roman_numeral),
                "primary": True
            }
            ],
        "key": "Footnotes on Teshuvot haRashba part {}".format(roman_numeral),
        "sectionNames": [
            "Teshuva",
            "Part"
            ]
        }
    }



def create_text(version_title, version_source, text):
    return {
            "versionTitle": version_title,
            "versionSource": version_source,
            "language": "he",
            "text": text
        }



def create_links(footnotes, roman_numeral):
    list_of_links = []
    for index, siman in enumerate(footnotes):
        for text in siman:
            if text:
                list_of_links.append( {
                        "refs": [
                                "Footnotes on Teshuvot haRashba part {}.{}".format(roman_numeral,index+1),
                                "Teshuvot haRashba part {}.{}".format(roman_numeral,index+1)
                            ],
                        "type": "Footnotes",
                        "auto": False,
                        "generated_by": "Joshua",
                                        })

    return list_of_links


def post_the_links(list_of_links):
    for link in list_of_links:
        functions.post_link(link)


rashba_comment_footnotes_4 = parseRashba7.parse('rashba4cmnt.txt')
post_index_and_text(rashba_comment_footnotes_4, four_dict)
list_of_links = create_links(rashba_comment_footnotes_4)