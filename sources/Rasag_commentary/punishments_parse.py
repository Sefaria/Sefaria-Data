# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode


def parse(file_name, regexp):
    the_whole_thing, section, mitzvah = [], [], []
    last_index = 1
    commentary = False

    with codecs.open(file_name, 'r', 'utf-8') as the_file:
        for each_line in the_file:

            if "@99" in each_line:
                section.append(mitzvah)
                the_whole_thing.append(section)
                section, mitzvah = [], []
                commentary = True

            elif "@00" in each_line:
                section.append(mitzvah)
                mitzvah = []
                if commentary:
                    last_index = fill_in_missing_sections_and_updated_last(each_line, section, regexp, [], last_index)
                    print last_index

            else:
                mitzvah.append(each_line)

    section.append(mitzvah)
    the_whole_thing.append(section)
    return the_whole_thing


def fill_in_missing_sections_and_updated_last(each_line, base_list, this_regex, filler, last_index):
    match_object = this_regex.search(each_line)
    string_of_mitzvot = match_object.group(1)
    string_of_mitzvot = string_of_mitzvot.strip()
    list_of_mitzvot = string_of_mitzvot.split()
    current_index = util.getGematria(list_of_mitzvot[0])
    diff = current_index - last_index
    while diff > 1:
        base_list.append(filler)
        diff -= 1
    return current_index