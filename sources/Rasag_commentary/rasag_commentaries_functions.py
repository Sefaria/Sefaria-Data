# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from parsing_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode


def create_text(jagged_array):
    return {
        "versionTitle": "Sefer Hamitzvot L'Rasag, Warsaw, 1914",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002027638",
        "language": "he",
        "text": jagged_array
    }


def create_links(rasag_commetary_ja, section_name):
    list_of_links = []
    base_text_mitzvah = 0
    number_of_comments = 0

    for mitzvah_index, mitzvah in enumerate(rasag_commetary_ja):

        if not mitzvah:
            list_of_links.append(create_link_dicttionary(section_name, base_text_mitzvah+1, number_of_comments+1, mitzvah_index+1))

        for comment_index, comment in enumerate(mitzvah):
            base_text_mitzvah = mitzvah_index
            number_of_comments = comment_index

        if mitzvah:
            list_of_links.append(create_link_dicttionary(section_name, base_text_mitzvah+1, number_of_comments+1, mitzvah_index+1))

    return list_of_links


def create_link_dicttionary(section_name, base_text_section, base_text_comment, referenced_section):
    return {
                "refs": [
                        "Commentary on Sefer Hamitzvot of Rasag, {}.{}".format(section_name, base_text_section),
                        "Sefer_Hamitzvot_of_Rasag, {}.{}".format(section_name, referenced_section)
                    ],
                "type": "commentary",
        }