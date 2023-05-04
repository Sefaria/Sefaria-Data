# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from parsing_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode
from fuzzywuzzy import fuzz
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys


def create_index():
    lechem_shamayim_schema = create_schema()
    lechem_shamayim_schema.validate()
    index = {
        "title": "Lechem Shamayim on Pirkei Avot",
        "categories": ["Commentary2", "Pirkei Avot", "Lechem Shamayim"],
        "schema": lechem_shamayim_schema.serialize()
    }
    return index

def create_schema():
    ls_schema = JaggedArrayNode()
    ls_schema.add_title('Lechem Shamayim on Pirkei Avot', 'en', primary=True)
    ls_schema.add_title(u'לחם שמים על פרקי אבות', 'he', primary=True)
    ls_schema.key = 'Lechem Shamayim on Pirkei Avot'
    ls_schema.depth = 3
    ls_schema.addressTypes = ["Integer", "Integer", "Integer"]
    ls_schema.sectionNames = ["Perek", "Mishna", "Comment"]
    return ls_schema


def parse_and_post(file_name):
    mishna_number_regex = regex.compile(u'([\u05d0-\u05ea]{1,3})')
    lechem_shamayim_on_avot, perek_level_list, mishna_level_list = [], [], []
    new_perek, first_perek = True, True
    last_mishna = 0
    with codecs.open(file_name, 'r', 'utf-8') as the_file:
        for each_line in the_file:

            if "@00" in each_line:
                if not first_perek:
                    perek_level_list.append(mishna_level_list)
                    lechem_shamayim_on_avot.append(perek_level_list)
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

        lechem_shamayim_on_avot.append(perek_level_list)
        post_the_text(lechem_shamayim_on_avot)
    return lechem_shamayim_on_avot


def clean_up_string(string):
    string = add_bold(string, ['@11', '@44'], ['@33', '@55'])
    string = make_small(string, ['@77'], ['@88'])
    string = remove_substrings(string, ['*'])
    return string


def remove_substrings(string, list_of_tags):
    for tag in list_of_tags:
        string = string.replace(tag, '')
    return string


def add_bold(string, list_of_opening_tags, list_of_closing_tags):
    for tag in list_of_opening_tags:
        string = string.replace(tag, '<b>')
    for tag in list_of_closing_tags:
        string = string.replace(tag, '</b>')
    return string


def make_small(string, list_of_opening_tags, list_of_closing_tags):
    for tag in list_of_opening_tags:
        string = string.replace(tag, '<small>')
    for tag in list_of_closing_tags:
        string = string.replace(tag, '</small>')
    return string


def post_the_text(ja):
    testing_file = codecs.open("testing_file.txt", 'w', 'utf-8')
    util.jagged_array_to_file(testing_file, ja, ['Perek', 'Mishna','Comment'])
    testing_file.close()
    ref = create_ref()
    text = create_text(ja)
    functions.post_text(ref, text)


def create_ref():
    ref = 'Lechem Shamayim on Pirkei Avot'
    return ref


def create_text(jagged_array):
    return {
        "versionTitle": "Ets Avot, Lechem Shamayim; Krakow, 1883.",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001277616",
        "language": "he",
        "text": jagged_array
    }


def create_links(ls_ja):
    list_of_links = []
    for perek_index, perek in enumerate(ls_ja):
        for mishna_index, mishna in enumerate(perek):
            for comment_index, comment in enumerate(mishna):
                list_of_links.append(create_link_dicttionary(perek_index+1, mishna_index+1, comment_index+1))
    functions.post_link(list_of_links)


def create_link_dicttionary(perek_bumber, mishna_number, comment_index):
    return {
                "refs": [
                        "Pirkei Avot {}.{}".format(perek_bumber, mishna_number),
                        "Lechem Shamayim on Pirkei Avot {}.{}.{}".format(perek_bumber, mishna_number, comment_index)
                    ],
                "type": "commentary",
        }