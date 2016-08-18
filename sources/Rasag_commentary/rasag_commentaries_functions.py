# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode





def parse():

    with codecs.open('ralbag_on_esther.txt', 'r', 'utf-8') as the_file:
        for each_line in the_file:
            print each_line




def fill_in_missing_sections_and_updated_last(each_line, base_list, this_regex, filler, last_index):
    match_object = this_regex.search(each_line)
    current_index = util.getGematria(match_object.group(1))
    diff = current_index - last_index
    while diff > 1:
        base_list.append(filler)
        diff -= 1
    return current_index


def create_text(jagged_array):
    return {
        "versionTitle": "",
        "versionSource": "",
        "language": "he",
        "text": jagged_array
    }


def create_links(rasag_commetary_ja):
    list_of_links = []
    base_text_mitzvah = 0
    number_of_comments = 0

    for mitzvah_index, mitzvah in enumerate(rasag_commetary_ja):

        if not mitzvah:
            list_of_links.append(create_link_dicttionary(base_text_mitzvah+1, number_of_comments+1, mitzvah_index+1))

        for comment_index, comment in enumerate(mitzvah):
            base_text_mitzvah = mitzvah_index
            number_of_comments = comment_index

        if mitzvah:
            list_of_links.append(create_link_dicttionary(base_text_mitzvah+1, number_of_comments+1, mitzvah_index+1))

    return list_of_links


def create_link_dicttionary(base_text_section, base_text_comment, referenced_section):
    if base_text_comment == 1:
        comment_string = ''
    else:
        comment_string = '-{}'.format(base_text_comment)
    return {
                "refs": [
                        "Base Text, named section.{}.1{}".format(base_text_section, comment_string),
                        "The referenced work, named section.{}".format(referenced_section)
                    ],
                "type": "commentary",
        }