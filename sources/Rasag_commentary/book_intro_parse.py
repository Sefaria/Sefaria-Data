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
    chapter_number = regex.compile('@00([\u05d0-\u05ea]{1,2})')
    chapter_index = 1
    section, comment = [], []

    seven, shorashim, nine = [], [], []
    chapter_seven_intro = True

    with codecs.open(file_name, 'r', 'utf-8') as the_file:
        for each_line in the_file:

            if "@00" in each_line:
                if chapter_index != 7 and chapter_index != 9:
                    section.append(comment)
                    comment = []

                elif chapter_index == 7:
                    shorashim.append(comment)
                    seven.append(shorashim)
                    section.append(seven)
                    comment = []

                elif chapter_index == 9:
                    nine.append(comment)
                    section.append(nine)
                    comment = []

                match_object = chapter_number.search(each_line)
                chapter_index = util.getGematria(match_object.group(1))

            elif chapter_index != 7 and chapter_index != 9:
                each_line = clean_up(each_line)
                comment.append(each_line)

            elif chapter_index == 7:
                if "@01" in each_line:
                    if chapter_seven_intro:
                        seven.append(comment)
                        comment = []
                        chapter_seven_intro = False
                    else:
                        shorashim.append(comment)
                        comment = []
                else:
                    comment.append(each_line)

            elif chapter_index == 9:
                if "@01" in each_line:
                    nine.append(comment)
                    comment = []

                else:
                    comment.append(each_line)

    section.append(comment)
    return section


def clean_up(string):
    string = remove_substrings(string, ["@22"])
    return string


def remove_substrings(string, list_of_tags):
    for tag in list_of_tags:
        string = string.replace(tag, '')
    return string

