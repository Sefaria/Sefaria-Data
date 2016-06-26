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
                each_line = each_line.strip( '+' )
                second_level_list.append(each_line)

        while siman_number > count:
            rashba_section_seven.append(None)
            count += 1

        rashba_section_seven.append(second_level_list)
    return rashba_section_seven


rashba_section_seven = parse('rashba7.txt')


rashba_text = {
    "versionTitle": "Warsaw, 1868",
    "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001124680",
    "language": "he",
    "text": rashba_section_seven
}

rashba_index = {
    "pubDate": "1470",
    "title": "Teshuvot haRashba part VII",
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
            "text": "Teshuvot helek Sheva"
        },
        {
            "lang": "en",
            "text": "shut harashba part seven"
        },
        {
            "lang": "he",
            "text": u"\u05e9\u05d5\u0022\u05ea \u05d4\u05e8\u05e9\u05d1\u0022\u05d0 \u05d7\u05dc\u05e7 \u05d6",
            "primary": True
        },
        {
            "lang": "he",
            "text": u"\u05e9\u05d0\u05dc\u05d5\u05ea \u05d5\u05ea\u05e9\u05d5\u05d1\u05d5\u05ea \u05d4\u05e8\u05e9\u05d1\u0022\u05d0 \u05d7\u05dc\u05e7 \u05d6"
        },
        {
            "lang": "he",
            "text": u"\u05e9\u05d5\u0022\u05ea \u05d4\u05e8\u05e9\u05d1\u0022\u05d0 \u05d6"
        },
        {
            "lang": "en",
            "text": "Teshuvot haRashba part VII",
            "primary": True
        }
        ],
    "key": "Teshuvot haRashba part VII",
    "sectionNames": [
        "Teshuva",
        "Part"
        ]
    }
}


functions.post_index(rashba_index)
functions.post_text('Teshuvot haRashba part VII', rashba_text)
