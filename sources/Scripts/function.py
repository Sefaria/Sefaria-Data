# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util



def parse(file1):
    line_with_siman_number = regex.compile(u'\u05e1\u05d9\u05de\u05df\s([\u05d0-\u05ea]{1,5})')

    rashba_section_seven = []
    second_level_list = []
    first_time = True
    siman_number, count = 0, 1

    with codecs.open(file1, 'r', 'utf-8') as the_file:
        for each_line in the_file:

            each_line = each_line.strip()
            search_object = line_with_siman_number.match(each_line)

            if search_object:
                if not first_time:
                    while siman_number > count:
                        rashba_section_seven.append([])
                        count += 1

                    rashba_section_seven.append(second_level_list)
                    count += 1
                    second_level_list = []

                siman_number = util.getGematria(search_object.group(1))
                first_time = False

            elif not each_line:
                continue

            else:
                second_level_list.append(each_line)

        while siman_number > count:
            rashba_section_seven.append([])
            count += 1

        rashba_section_seven.append(second_level_list)
    return rashba_section_seven


def clean_up_string(each_line):
    each_line = each_line.strip('+')
    result = ''.join(char for char in each_line if not char.isdigit())
    return result


def create_dict(roman_numeral, transliterated, hebrew_letter, number, version_title, version_source):
    return {
            'roman numeral': roman_numeral,
            'transliterated': transliterated,
            'hebrew letter':hebrew_letter,
            'number': number,
            'version title': version_title,
            'version source': version_source
        }


def create_index(dictionary, footnotes = '', footnotes_hebrew = ''):
    return {
        "pubDate": "1470",
        "title": "{}Teshuvot haRashba part {}".format(footnotes, dictionary['roman numeral']),
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
                "text": "{}Teshuvot haRashba helek {}".format(footnotes, dictionary['transliterated'])
            },
            {
                "lang": "en",
                "text": "{}Teshuvot haRashba part {}".format(footnotes, dictionary['number'])
            },
            {
                "lang": "he",
                "text": u"{}\u05e9\u05d5\u0022\u05ea \u05d4\u05e8\u05e9\u05d1\u0022\u05d0 \u05d7\u05dc\u05e7 {}".format(footnotes_hebrew, dictionary['hebrew letter']),
                "primary": True
            },
            {
                "lang": "he",
                "text": u"{}\u05e9\u05d0\u05dc\u05d5\u05ea \u05d5\u05ea\u05e9\u05d5\u05d1\u05d5\u05ea \u05d4\u05e8\u05e9\u05d1\u0022\u05d0 \u05d7\u05dc\u05e7 {}".format(footnotes_hebrew, dictionary['hebrew letter'])
            },
            {
                "lang": "he",
                "text": u"{}\u05e9\u05d5\u0022\u05ea \u05d4\u05e8\u05e9\u05d1\u0022\u05d0 {}".format(footnotes_hebrew, dictionary['hebrew letter'])
            },
            {
                "lang": "en",
                "text": "{}Teshuvot haRashba part {}".format(footnotes, dictionary['roman numeral']),
                "primary": True
            }
            ],
        "key": "{}Teshuvot haRashba part {}".format(footnotes, dictionary['roman numeral']),
        "sectionNames": [
            "Teshuva",
            "Part"
            ]
        }
    }




def create_text(dictionary, text):
    return {
            "versionTitle": dictionary['version title'],
            "versionSource": dictionary['version source'],
            "language": "he",
            "text": text
        }


def create_links(teshuvot_ja, roman_numeral):
    list_of_links = []
    for siman_index, siman in enumerate(teshuvot_ja):
        for text_index, text in enumerate(siman):
            if text:
                list_of_footnote_tags = regex.findall(r'\d+',text)
                if list_of_footnote_tags:
                    for number in list_of_footnote_tags:
                        list_of_links.append({
                            "refs": [
                                    "Footnotes on Teshuvot haRashba part {}.{}.{}".format(roman_numeral,siman_index+1,number),
                                    "Teshuvot haRashba part {}.{}.{}".format(roman_numeral,siman_index+1, text_index+1)
                                ],
                            "type": "Footnotes",
                            "auto": False,
                            "generated_by": "Joshua",
                                            })

    return list_of_links
