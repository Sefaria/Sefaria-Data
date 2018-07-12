# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode

os_hagah = regex.compile(u'@22\([\u05d0-\u05ea]{1,2}\)')
gemara_internal_links = regex.compile(u'(@13\(\u05d3\u05e3)\s[\u05d0-\u05ea]{1,2}\s\u05e2\u0022(?:\u05d0|\u05d1)\)')
gemara_external_links = regex.compile(u'\((@13)([\u05d0-\u05ea]{3,15})\s[\u05d0-\u05ea]{1,2}\s\u05e2\u0022(?:\u05d0|\u05d1)\)')

def create_index():
    rif = create_schema()
    rif.validate()
    index = {
        "title": "Rif_Nedarim",
        "categories": ["Talmud", "Rif", "Seder Nashim"],
        "schema": rif.serialize()
    }
    return index


def create_schema():
    rif_on_nedarim = JaggedArrayNode()
    rif_on_nedarim.add_title('Rif_Nedarim', 'en', primary=True)
    rif_on_nedarim.add_title(u'רי"ף נדרים', 'he', primary=True)
    rif_on_nedarim.key = 'Rif_Nedarim'
    rif_on_nedarim.depth = 2
    rif_on_nedarim.addressTypes = ["Talmud", "Integer"]
    rif_on_nedarim.sectionNames = ["Daf", "Line"]
    return rif_on_nedarim


def parse():
    rif_on_nedarim, amud = [], []

    with codecs.open('rif_on_nedarim.txt', 'r', 'utf-8') as the_file:
        for each_line in the_file:

            if "@20" in each_line:
                list_of_pages = each_line.split("@20")
                for index, page in enumerate(list_of_pages):
                    if ":" in page:
                        list_of_comments = page.split("~")
                        for comment in list_of_comments:
                            comment = clean_up(comment)
                            if comment:
                                amud.append(comment)
                    else:
                        page = clean_up(page)
                        if page:
                            amud.append(page)

                    if index < (len(list_of_pages)-1):
                        rif_on_nedarim.append(amud)
                        amud = []

            else:
                if ":" in each_line:
                    list_of_comments = each_line.split("~")
                    for comment in list_of_comments:
                        comment = clean_up(comment)
                        if comment:
                            amud.append(comment)
                else:
                    each_line = clean_up(each_line)
                    if each_line:
                        amud.append(each_line)

    rif_on_nedarim.append(amud)
    return rif_on_nedarim


def clean_up(string):
    string = string.strip()
    string = add_bold(string, ['@11'], ["@33"])
    string = remove_os_hagah_tags(string)
    string = internal_links(string)
    string = external_links(string)
    string = remove_substrings(string, ['@88', '@00', '@99'])
    return string


def add_bold(string, list_of_opening_tags, list_of_closing_tags):
    for tag in list_of_opening_tags:
        string = string.replace(tag, '<b>')
    for tag in list_of_closing_tags:
        string = string.replace(tag, '</b>')
    return string


def remove_os_hagah_tags(string):
    list_of_tags = os_hagah.findall(string)
    for tag in list_of_tags:
        string = string.replace(tag, '')
    return string


def internal_links(string):
    list_of_tags = gemara_internal_links.findall(string)
    for tag in list_of_tags:
        string = string.replace(tag, u'(נדרים')
    return string


def external_links(string):
    list_of_tags = gemara_external_links.findall(string)
    for tag in list_of_tags:
        string = string.replace(tag[0], '')
    return string


def remove_substrings(string, list_of_tags):
    for tag in list_of_tags:
        string = string.replace(tag, '')
    return string


def create_text(jagged_array):
    return {
        "versionTitle": "Vilna Edition",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "language": "he",
        "text": jagged_array
    }
