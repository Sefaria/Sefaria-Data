# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
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





def parse_and_post(file_name):

    rb_yonah_on_avot, perek_level_list = [], []
    new_perek, first_perek = True, True
    with codecs.open(file_name, 'r', 'utf-8') as the_file:
        for each_line in the_file:

            if "@00" in each_line:
                if not first_perek:
                    rb_yonah_on_avot.append(perek_level_list)
                    perek_level_list = []
                else:
                    first_perek = False

            elif "@22" in each_line:
                """
                play catch up
                """
                continue

            else:
                perek_level_list.append(each_line)

        perek_level_list.append(each_line)
        rb_yonah_on_avot.append(perek_level_list)
        post_the_text(rb_yonah_on_avot)



def post_the_text(ja):
    testing_file = codecs.open("testing_file.txt", 'w', 'utf-8')
    util.jagged_array_to_file(testing_file, ja, ['perek', 'Mishna'])
    testing_file.close()