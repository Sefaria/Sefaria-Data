# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode


bach = regex.compile(u'\([#\*][\u05d0-\u05ea]{1,2}\)')

def create_index():
    rif = create_schema()
    rif.validate()
    index = {
        "title": "Rif_Megillah",
        "categories": ["Talmud", "Rif", "Seder Moed"],
        "schema": rif.serialize()
    }
    return index


def create_schema():
    rif_on_megillah = JaggedArrayNode()
    rif_on_megillah.add_title('Rif_Megillah', 'en', primary=True)
    rif_on_megillah.add_title(u'רי"ף מגילה', 'he', primary=True)
    rif_on_megillah.key = 'Rif_Megillah'
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
                            comment = clean_up(comment)
                            if comment:
                                amud.append(comment)
                    else:
                        page = clean_up(page)
                        if page:
                            amud.append(page)

                    if index < (len(list_of_pages)-1):
                        rif_on_megillah.append(amud)
                        amud = []

            else:
                if ":" in each_line:
                    list_of_comments = each_line.split(":")
                    for comment in list_of_comments:
                        comment = clean_up(comment)
                        if comment:
                            amud.append(comment)
                else:
                    each_line = clean_up(each_line)
                    if each_line:
                        amud.append(each_line)

    return rif_on_megillah


def clean_up(string):
    string = string.strip()
    string = add_bold(string, ['@44'], ["@55"])
    string = remove_bach_tags(string)
    string = remove_substrings(string, [u'\u00B0'])
    return string


def add_bold(string, list_of_opening_tags, list_of_closing_tags):
    for tag in list_of_opening_tags:
        string = string.replace(tag, '<b>')
    for tag in list_of_closing_tags:
        string = string.replace(tag, '</b>')
    return string


def remove_bach_tags(string):
    list_of_tags = bach.findall(string)
    for tag in list_of_tags:
        string = string.replace(tag, '')
    return string


def remove_substrings(string, list_of_tags):
    for tag in list_of_tags:
        string = string.replace(tag, '')
    return string


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
