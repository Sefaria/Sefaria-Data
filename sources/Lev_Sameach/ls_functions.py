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
    lev_sameach_schema = create_schema()
    lev_sameach_schema.validate()
    index = {
        "title": "Lev Sameach",
        "categories": ["Commentary2", "Halacha", "Lev Sameach"],
        "schema": lev_sameach_schema.serialize()
    }
    return index


def create_schema():
    lev_sameach = SchemaNode()
    lev_sameach.add_title('Lev Sameach', 'en', primary=True)
    lev_sameach.add_title(u'לב שמח', 'he', primary=True)
    lev_sameach.key = 'Lev Sameach'
    lev_sameach.append(create_shorash_node())
    lev_sameach.append(create_mitzvah_node('Positive Commandments', u'מצוה עשה'))
    lev_sameach.append(create_mitzvah_node('Negative Commandments', u'מצוה לא תעשה'))
    return lev_sameach


def create_shorash_node():
    shorash = JaggedArrayNode()
    shorash.add_title('Shorashim', 'en', primary=True)
    shorash.add_title(u'שורשים', 'he', primary=True)
    shorash.key = 'Shorashim'
    shorash.depth = 2
    shorash.addressTypes = ["Integer", "Integer"]
    shorash.sectionNames = ["Shoresh", "Comment"]
    return shorash

def create_mitzvah_node(en_name, he_name):
    mitzvah = JaggedArrayNode()
    mitzvah.add_title(en_name, 'en', primary=True)
    mitzvah.add_title(he_name, 'he', primary=True)
    mitzvah.key = en_name
    mitzvah.depth = 2
    mitzvah.addressTypes = ["Integer", "Integer"]
    mitzvah.sectionNames = ["Mitzvah", "Comment"]
    return mitzvah



def parse():
    lev_sameach, depth_two, depth_three = [], [], []
    first_text, shorash, commandments = True, True, False
    last_mitzvah = 0

    with codecs.open('lev_sameach.txt', 'r', 'utf-8') as the_file:
        for each_line in the_file:
            if "@00" in each_line:
                depth_two.append(depth_three)
                lev_sameach.append(depth_two)
                depth_two, depth_three = [], []
                last_mitzvah = 0
                first_text = True
                if shorash:
                    commandments = True
                    shorash = False

            elif shorash:
                if "@22" in each_line:
                    if not first_text:
                        depth_two.append(depth_three)
                        each_line = clean_up_string(each_line)
                        depth_three = [each_line]
                    else:
                        first_text = False

                else:
                    each_line = clean_up_string(each_line)
                    depth_three.append(each_line)

            elif commandments:
                if "@22" in each_line:
                    if not first_text:
                        depth_two.append(depth_three)

                    else:
                        first_text = False

                    last_mitzvah = fill_in_missing_sections_and_update_last(each_line, depth_two, mitzvah_number, [], last_mitzvah)
                    each_line = clean_up_string(each_line, mitzvot=True)
                    depth_three = [each_line]

                else:
                    each_line = clean_up_string(each_line, mitzvot=True)
                    depth_three.append(each_line)

    lev_sameach.append(depth_two)
    return lev_sameach


def fill_in_missing_sections_and_update_last(each_line, base_list, this_regex, filler, last_index):
    match_object = this_regex.search(each_line)
    current_index = util.getGematria(match_object.group(1))
    diff = current_index - last_index
    while diff > 1:
        base_list.append(filler)
        diff -= 1
    return current_index


def clean_up_string(string, mitzvot=False):
    string = add_bold(string, ['@11', '@22', '@44'], ['@33', '@55'])
    if mitzvot:
        match_object = mitzvah_number.search(string)
        if match_object:
            string = string.replace(match_object.group(0), '', 1)
    return string


def add_bold(string, list_of_opening_tags, list_of_closing_tags):
    for tag in list_of_opening_tags:
        string = string.replace(tag, '<b>')
    for tag in list_of_closing_tags:
        string = string.replace(tag, '</b>')
    return string


def create_links(lev_sameach_ja):
    rambam = 'Sefer_HaMitzvot_LaRambam,_Shorashim'
    ramban = 'Hasagot_HaRamban_al_Sefer_HaMitzvot,_Shorashim'
    ramban_shoreshim = [1, 2, 3, 4, 5, 6, 8, 9, 12, 14]
    list_of_links = []
    for shoresh_index, shoresh in enumerate(lev_sameach_ja):
        list_of_links.append(create_link_dicttionary(shoresh_index + 1, rambam))
        if shoresh_index + 1 in ramban_shoreshim:
            list_of_links.append(create_link_dicttionary(shoresh_index + 1, ramban))

    return list_of_links


def create_link_dicttionary(shoresh_number, ramban_or_ramban):
    return {
        "refs": [
            "{}.{}.1".format(ramban_or_ramban, shoresh_number),
            "Lev Sameach,_Shorashim.{}.1".format(shoresh_number)
        ],
        "type": "commentary",
    }


def create_text(jagged_array):
    return {
        "versionTitle": "Sefer HaMitzvot, Warsaw 1883",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001769510",
        "language": "he",
        "text": jagged_array
    }
