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
    ralbag = create_schema()
    ralbag.validate()
    index = {
        "title": "Ralbag Ruth",
        "categories": ["Commentary2", "Tanakh", "Ralbag"],
        "schema": ralbag.serialize()
    }
    return index


def create_schema():
    ralbag_on_ruth = SchemaNode()
    ralbag_on_ruth.add_title('Ralbag Ruth', 'en', primary=True)
    ralbag_on_ruth.add_title(u'רלב"ג רות', 'he', primary=True)
    ralbag_on_ruth.key = 'Ralbag Ruth'
    ralbag_on_ruth.append(create_commentary_node())
    ralbag_on_ruth.append(create_toalot_node())
    return ralbag_on_ruth


def create_commentary_node():
    commentary = JaggedArrayNode()
    commentary.default = True
    commentary.key = 'default'
    commentary.depth = 3
    commentary.addressTypes = ["Integer", "Integer", "Integer"]
    commentary.sectionNames = ["Perek", "Pasuk", "Comment"]
    return commentary


def create_toalot_node():
    toalot = JaggedArrayNode()
    toalot.add_title('Benefits', "en", primary=True)
    toalot.add_title(u'תועלות', "he", primary=True)
    toalot.key = 'Benefits'
    toalot.depth = 1
    toalot.addressTypes = ["Integer"]
    toalot.sectionNames = ["Comment"]
    return toalot


def parse():
    the_whole_thing = {}
    commentary_on_ruth, perek, pasuk = [], [], []
    toalot = []
    toalot_section = False
    last_pasuk = 1
    pasuk_number_regex = regex.compile(u'@22([\u05d0-\u05ea]{1,2})')

    with codecs.open('ralbag_on_ruth.txt', 'r', 'utf-8') as the_file:
        for each_line in the_file:

            if "@00" in each_line:
                toalot_section = True
                perek.append(pasuk)
                commentary_on_ruth.append(perek)
                the_whole_thing['Commentary'] = commentary_on_ruth

            elif "@01" in each_line:
                perek.append(pasuk)
                commentary_on_ruth.append(perek)
                perek, pasuk = [], []
                last_pasuk = 1

            elif "@22" in each_line:
                perek.append(pasuk)
                last_pasuk = fill_in_missing_sections_and_updated_last(each_line, perek, pasuk_number_regex, [], last_pasuk)
                pasuk = []

            elif toalot_section:
                toalot.append(each_line)

            else:
                pasuk.append(each_line)

    the_whole_thing['Benefits'] = toalot
    return the_whole_thing


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
        "versionTitle": "Perush al Hamesh Megillot, Konigsberg, 1860",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001970747",
        "language": "he",
        "text": jagged_array
    }


def create_links(ralbag_ja):
    list_of_links = []
    for perek_index, perek in enumerate(ralbag_ja):
        for pasuk_index, pasuk in enumerate(perek):
            for comment_index, comment in enumerate(pasuk):
                list_of_links.append(create_link_dicttionary(perek_index+1, pasuk_index+1, comment_index+1))
    return list_of_links


def create_link_dicttionary(perek_bumber, mishna_number, comment_index):
    return {
                "refs": [
                        "Ruth.{}.{}".format(perek_bumber, mishna_number),
                        "Ralbag Ruth.{}.{}.{}".format(perek_bumber, mishna_number, comment_index)
                    ],
                "type": "commentary",
        }