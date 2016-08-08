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
        "title": "Ralbag on Ruth",
        "categories": ["Commentary2", "", "Ralbag"],
        "schema": ralbag.serialize()
    }
    return index


def create_schema():
    ralbag_on_ruth = SchemaNode()
    ralbag_on_ruth.add_title('Ralbag on Ruth', 'en', primary=True)
    ralbag_on_ruth.add_title(u'רלב"ג על רות', 'he', primary=True)
    ralbag_on_ruth.key = 'Ralbag on Ruth'
    ralbag_on_ruth.append(create_commentary_node())
    ralbag_on_ruth.append(create_toalot_node())
    return ralbag_on_ruth


def create_commentary_node():
    commentary = JaggedArrayNode()
    commentary.default = True
    commentary.key = 'default'
    commentary.depth = 3
    commentary.addressTypes = ["Integer", "Integer"]
    commentary.sectionNames = ["Perek", "Pasuk"]
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
    the_whole_thing = []
    commentary_on_ruth, perek, pasuk = [], [], []
    toalot = []
    toalot_section = False

    with codecs.open('ralbag_on_ruth.txt', 'r', 'utf-8') as the_file:
        for each_line in the_file:

            if "@00" in each_line:
                toalot_section = True
                perek.append(pasuk)
                commentary_on_ruth.append(perek)
                the_whole_thing.append(commentary_on_ruth)

            elif "@01" in each_line:
                perek.append(pasuk)
                commentary_on_ruth.append(perek)
                perek, pasuk = [], []

            elif "@22" in each_line:
                perek.append(pasuk)

                #play catch up

                pasuk = []

            elif toalot_section:
                toalot.append(each_line)

            else:
                pasuk.append(each_line)

    the_whole_thing.append(toalot)
    return the_whole_thing


def clean_up(string):
    string = string.strip()
    string = add_bold(string, ['@44'], ["@55"])
    string = remove_substrings(string, [u'\u00B0'])
    return string


def add_bold(string, list_of_opening_tags, list_of_closing_tags):
    for tag in list_of_opening_tags:
        string = string.replace(tag, '<b>')
    for tag in list_of_closing_tags:
        string = string.replace(tag, '</b>')
    return string


def remove_substrings(string, list_of_tags):
    for tag in list_of_tags:
        string = string.replace(tag, '')
    return string


def create_text(jagged_array):
    return {
        "versionTitle": "Perush al Hamesh Megillot, Konigsberg, 1860",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001970747",
        "language": "he",
        "text": jagged_array
    }
