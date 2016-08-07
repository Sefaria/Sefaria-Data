# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode


mitzvah_number = regex.compile(u'@88\(([\u05d0-\u05ea]{1,4})\)')

def create_index():
    rif = create_schema()
    rif.validate()
    index = {
        "title": "",
        "categories": ["Commentary2", "", ""],
        "schema": rif.serialize()
    }
    return index


def create_schema():
    rif_on_megillah = JaggedArrayNode()
    rif_on_megillah.add_title('', 'en', primary=True)
    rif_on_megillah.add_title('', 'he', primary=True)
    rif_on_megillah.key = ''
    rif_on_megillah.depth = 2
    rif_on_megillah.addressTypes = ["Talmud", "Integer"]
    rif_on_megillah.sectionNames = ["Daf", "Line"]
    return rif_on_megillah


def parse():
    rif_on_megillah, amud = [], []

    with codecs.open('rif_on_megillah.txt', 'r', 'utf-8') as the_file:
        for each_line in the_file:

            if "@20" in each_line:
                list_of_pages = each_line.split("@20")
                for index, page in enumerate(list_of_pages):
                    if ":" in page:
                        list_of_comments = page.split(":")
                        for comment in list_of_comments:
                            amud.append(comment)
                    else:
                        amud.append(page)

                    if index < (len(list_of_pages)-1):
                        rif_on_megillah.append(amud)
                        amud = []

            else:
                if ":" in each_line:
                    list_of_comments = each_line.split(":")
                    for comment in list_of_comments:
                        amud.append(comment)
                else:
                    amud.append(each_line)

    return rif_on_megillah


def fill_in_missing_sections_and_update_last(each_line, base_list, this_regex, filler, last_index):
    match_object = this_regex.search(each_line)
    current_index = util.getGematria(match_object.group(1))
    diff = current_index - last_index
    while diff > 1:
        base_list.append(filler)
        diff -= 1
    return current_index


def create_links(eee_ja):
    list_of_links = []
    for perek_index, perek in enumerate(eee_ja):
        for pasuk_index, pasuk in enumerate(perek):
            for comment_index, comment in enumerate(pasuk):
                list_of_links.append(create_link_dicttionary(perek_index+1, pasuk_index+1, comment_index+1))
    return list_of_links


def create_link_dicttionary(perek, pasuk, comment):
    return {
        "refs": [
            "",
            ""
        ],
        "type": "commentary",
    }


def create_text(jagged_array):
    return {
        "versionTitle": "",
        "versionSource": "",
        "language": "he",
        "text": jagged_array
    }
