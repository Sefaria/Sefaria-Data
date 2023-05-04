# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from parsing_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode


def parse(file_name):
    the_whole_thing, section, comment = [], [], []
    intro = True

    with codecs.open(file_name, 'r', 'utf-8') as the_file:
        for each_line in the_file:

            if "@00" in each_line:
                if intro:
                    the_whole_thing.append(comment)
                    comment = []
                    intro = False
                else:
                    section.append(comment)
                    comment = []

            else:
                each_line = clean_up(each_line)
                comment.append(each_line)


    section.append(comment)
    the_whole_thing.append(section)
    return the_whole_thing


def clean_up(string):
    string = remove_substrings(string, ["@22"])
    return string


def remove_substrings(string, list_of_tags):
    for tag in list_of_tags:
        string = string.replace(tag, '')
    return string

