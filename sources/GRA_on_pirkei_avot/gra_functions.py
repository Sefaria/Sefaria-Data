# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode


def create_index():
    gra_schema = create_schema()
    gra_schema.validate()
    index = {
        "title": "Gra on Pirkei Avot",
        "categories": ["Commentary2", "Pirkei Avot", "Gra"],
        "schema": gra_schema.serialize()
    }
    return index

def create_schema():
    gra_schema = JaggedArrayNode()
    gra_schema.add_title('Gra on Pirkei Avot', 'en', primary=True)
    gra_schema.add_title(u'גר"א על פרקי אבות', 'he', primary=True)
    gra_schema.key = 'Gra on Pirkei Avot'
    gra_schema.depth = 3
    gra_schema.addressTypes = ["Integer", "Integer", "Integer"]
    gra_schema.sectionNames = ["Perek", "Mishna", "Comment"]
    return gra_schema


def parse():
    mishna_number_regex = regex.compile(u'([\u05d0-\u05ea]{1,3})')
    gra_on_avot, perek_level_list, mishna_level_list = [], [], []
    new_perek, first_perek = True, True
    last_mishna = 0
    with codecs.open('gra_on_avot.txt', 'r', 'utf-8') as the_file:
        for each_line in the_file:

            if "@00" in each_line:
                if not first_perek:
                    perek_level_list.append(mishna_level_list)
                    gra_on_avot.append(perek_level_list)
                    perek_level_list, mishna_level_list = [], []
                    new_perek = True

                else:
                    first_perek = False

            elif "@22" in each_line:
                if not new_perek:
                    perek_level_list.append(mishna_level_list)
                    mishna_level_list = []

                    match_object = mishna_number_regex.search(each_line)
                    mishna_number = util.getGematria(match_object.group(1))
                    diff = mishna_number - last_mishna
                    while diff > 1:
                        perek_level_list.append([])
                        diff -= 1

                    last_mishna = mishna_number

                else:
                    new_perek = False
                    last_mishna = 1

            else:
                each_line = clean_up_string(each_line)
                mishna_level_list.append(each_line)


        gra_on_avot.append(perek_level_list)

    return gra_on_avot


def clean_up_string(string):
    string = add_bold(string, ['@11'], ['@33'])
    return string


def add_bold(string, list_of_opening_tags, list_of_closing_tags):
    for tag in list_of_opening_tags:
        string = string.replace(tag, '<b>')
    for tag in list_of_closing_tags:
        string = string.replace(tag, '</b>')
    return string

def create_links(gra_ja):
    list_of_links = []
    for perek_index, perek in enumerate(gra_ja):
        for mishna_index, mishna in enumerate(perek):
            for comment_index, comment in enumerate(mishna):
                list_of_links.append(create_link_dicttionary(perek_index+1, mishna_index+1, comment_index+1))
    functions.post_link(list_of_links)


def create_link_dicttionary(perek_bumber, mishna_number, comment_index):
    return {
                "refs": [
                        "Pirkei Avot {}.{}".format(perek_bumber, mishna_number),
                        "Gra on Pirkei Avot {}.{}.{}".format(perek_bumber, mishna_number, comment_index)
                    ],
                "type": "commentary",
        }

def create_text(jagged_array):
    return {
        "versionTitle": "Pirkei Avot with commentary of the Vilna Gaon, Vilna 1836",
        "versionSource": "http://dlib.rsl.ru/viewer/01006756620#?page=5",
        "language": "he",
        "text": jagged_array
    }
