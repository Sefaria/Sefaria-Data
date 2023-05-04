# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from parsing_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode


mitzvah_number = regex.compile(u'@88\(([\u05d0-\u05ea]{1,4})\)')

def create_index():
    eben_ezra = create_schema()
    eben_ezra.validate()
    index = {
        "title": "Eben Ezra on Lamentations",
        "categories": ["Commentary2", "Lamentations", "Eben Ezra"],
        "schema": eben_ezra.serialize()
    }
    return index


def create_schema():
    eben_ezra = SchemaNode()
    eben_ezra.add_title('Eben Ezra on Lamentations', 'en', primary=True)
    eben_ezra.add_title(u'אבן עזרא על איכה', 'he', primary=True)
    eben_ezra.key = 'Eben Ezra on Lamentations'
    eben_ezra.append(create_intro_node())
    eben_ezra.append(create_commentary_node())
    return eben_ezra


def create_intro_node():
    intro = JaggedArrayNode()
    intro.add_title('Introduction', 'en', primary=True)
    intro.add_title(u'הקדמה', 'he', primary=True)
    intro.key = 'Introduction'
    intro.depth = 1
    intro.addressTypes = ["Integer"]
    intro.sectionNames = ["Comment"]
    return intro

def create_commentary_node():
    commentary = JaggedArrayNode()
    commentary.default = True
    commentary.key = 'default'
    commentary.depth = 3
    commentary.addressTypes = ["Integer", "Integer", "Integer"]
    commentary.sectionNames = ["Perek", "Pasuk", "Comment"]
    commentary.toc_zoom = 2
    return commentary


def parse():
    mishna_number = regex.compile(u'@22([\u05d0-\u05ea]{1,2})')
    eben_ezra, perek, pasuk = [], [], []
    intro_with_commentary = []
    first_perek = True
    new_perek = True
    last_mishna = 0

    with codecs.open('eben_ezra_eicha.txt', 'r', 'utf-8') as the_file:
        for each_line in the_file:
            if "@00" in each_line:
                continue

            elif "@01" in each_line:
                if first_perek:
                    intro_with_commentary.append(pasuk)
                    first_perek = False
                else:
                    perek.append(pasuk)
                    eben_ezra.append(perek)
                    new_perek = True
                perek, pasuk = [], []

            elif "@22" in each_line:
                if not new_perek:
                    perek.append(pasuk)
                    pasuk = []
                else:
                    new_perek = False

                last_mishna = fill_in_missing_sections_and_update_last(each_line, perek, mishna_number, '', last_mishna)

            else:
                pasuk.append(each_line)

    eben_ezra.append(perek)
    intro_with_commentary.append(eben_ezra)
    return intro_with_commentary


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
            "Lamentations.{}.{}".format(perek, pasuk),
            "Eben_Ezra_on_Lamentations.{}.{}.{}".format(perek, pasuk, comment)
        ],
        "type": "commentary",
    }


def create_text(jagged_array):
    return {
        "versionTitle": "Ibn Ezra on Lamentations -- Wikitext",
        "versionSource": "https://he.wikisource.org/wiki/%D7%90%D7%91%D7%9F_%D7%A2%D7%96%D7%A8%D7%90_%D7%A2%D7%9C_%D7%9E%D7%92%D7%99%D7%9C%D7%AA_%D7%90%D7%99%D7%9B%D7%94",
        "language": "he",
        "text": jagged_array
    }
