# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from parsing_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode


bach = regex.compile(u'\([#\*]?[\u05d0-\u05ea]{1,2}\)')
ein_mishpat = regex.compile(u'@(?:11|22)[\u05d0-\u05ea]{1,2}')
gemara_internal_links = regex.compile(u'\((\u05d3\u05e3)\s[\u05d0-\u05ea]{1,2}\s\u05e2\u0022(?:\u05d0|\u05d1)\)')
gemara_external_links = regex.compile(u'\((@13)([\u05d0-\u05ea]{3,15})(\s[\u05d0-\u05ea]{1,8})?\s[\u05d0-\u05ea]{1,2}\s\u05e2\u0022(?:\u05d0|\u05d1)\)')

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
                        list_of_comments = page.split(u"~")
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

            elif "@00" in each_line:
                each_line = each_line.replace('@00', '')
                each_line = u'<small>{}</small>'.format(each_line)
                amud.append(each_line)

            else:
                if ":" in each_line:
                    list_of_comments = each_line.split(u"~")
                    for comment in list_of_comments:
                        comment = clean_up(comment)
                        if comment:
                            amud.append(comment)
                else:
                    each_line = clean_up(each_line)
                    if each_line:
                        amud.append(each_line)

    rif_on_megillah.append(amud)
    return rif_on_megillah


def clean_up(string):
    string = string.strip()
    string = add_bold(string, ['@44'], ["@55"])
    string = remove_bach_tags(string)
    string = remove_ein_mishpat_tags(string)
    string = internal_links(string)
    string = external_links(string)
    string = remove_substrings(string, [u'\u00B0', '@99', '*'])
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


def remove_ein_mishpat_tags(string):
    list_of_tags = ein_mishpat.findall(string)
    for tag in list_of_tags:
        string = string.replace(tag, '')
    return string


def internal_links(string):
    list_of_tags = gemara_internal_links.findall(string)
    for tag in list_of_tags:
        string = string.replace(tag, u'מגילה')
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
