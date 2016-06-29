# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util



def parse(file1):
    new_daf_tag = regex.compile(u'\u0040\u0032\u0032\u05d3\u05e3\s([\u05d0-\u05ea]{1,3})(\s\u05e2\u0022\u05d1)?')
    new_amud_tag = regex.compile(u'\u0040\u0032\u0032\u05e2\u0022\u05d1')
    placement = 0
    yad_ramah_on_sanhedrin = []
    second_level_list = []
    first_time = True
    daf_number, count = 0, 0

    with codecs.open(file1, 'r', 'utf-8') as the_file:
        for each_line in the_file:

            each_line = each_line.strip()
            each_line = each_line.replace(u'\u201d', u'\u0022')

            new_daf = new_daf_tag.match(each_line)
            new_amud = new_amud_tag.match(each_line)

            if new_daf or new_amud:

                if not first_time:
                    yad_ramah_on_sanhedrin.append(second_level_list)
                    count += 1
                    second_level_list = []

                if new_daf:
                    daf_number = util.getGematria(new_daf.group(1))

                if new_daf:
                    placement = daf_number*2-2
                    if new_daf.group(2):
                        placement += 1
                    while placement > count:
                        yad_ramah_on_sanhedrin.append([])
                        count += 1

                first_time = False

            elif not each_line:
                continue

            else:
                second_level_list.append(each_line)

    while placement > count:
        yad_ramah_on_sanhedrin.append([])
        count += 1

    yad_ramah_on_sanhedrin.append(second_level_list)

    return yad_ramah_on_sanhedrin


def create_dict(roman_numeral, transliterated, hebrew_letter, number, version_title, version_source):
    return {
            'roman numeral': roman_numeral,
            'transliterated': transliterated,
            'hebrew letter':hebrew_letter,
            'number': number,
            'version title': version_title,
            'version source': version_source
        }


def create_index():
    return {
        "pubDate": "~1200",
        "title": "Yad Ramah on Sanhedrin",
        "pubPlace": "Spain",
        "maps": [ ],
        "era": "Rishonim",
        "authors": [
            "Meir Abulafia"
        ],
        "categories": [
            "Commentary2",
            "Talmud"
            "Yad Ramah"
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
                "lang": "he",
                "text": u"\u05d9\u05d3 \u05e8\u05de\u05d4 \u05e2\u05dc \u05e1\u05e0\u05d4\u05d3\u05e8\u05d9\u05df",
                "primary": True
            },
            {
                "lang": "he",
                "text": u"\u05d9\u05d3 \u05e8\u05de\u05d4 \u05e2\u05dc \u05de\u05e1\u05db\u05ea \u05e1\u05e0\u05d4\u05d3\u05e8\u05d9\u05df",
            },
            {
                "lang": "en",
                "text": "Yad Ramah on Sanhedrin",
                "primary": True
            },
            {
                "lang": "en",
                "text": "Yad Ramah on Tractate Sanhedrin",
            }
            ],
        "key": "Yad Ramah on Sanhedrin",
        "sectionNames": [
            "Daf",
            "Comment"
            ]
        }
    }




def create_text(text):
    return {
            "versionTitle": "Yad Ramah Sanhedrin, Warsaw 1895 ed.",
            "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001063897",
            "language": "he",
            "text": text
        }
