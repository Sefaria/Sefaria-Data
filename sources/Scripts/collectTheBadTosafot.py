# -*- coding: utf-8 -*-
import codecs

import regex

from sefaria.model import *

from sources import functions


def collect_the_bad_tosafot():
    tosafot_references = get_commentator_reference_collection("Tosafot")
    put_bad_tosafot_in_file(tosafot_references)


def get_commentator_reference_collection(commentator):
    all_refs = []
    for mesechet in library.get_indexes_in_category('Bavli'):
        print (mesechet)
        all_refs.append(library.get_index(get_reference_name(commentator, mesechet)).all_segment_refs())
    return all_refs


def get_reference_name(commentator, mesechet):
    return "{} on {}".format(commentator, mesechet)

def put_bad_tosafot_in_file(tosafot_references):
    bad_tosafot = open('badTosafot.txt', 'w')
    two_dash_tosafot = open('twoDashTosafot.txt', 'w')
    tosafot_that_dont_exist = open('TosafotThatDontExist.txt', 'w')
    for mesechet in tosafot_references:
        for eachComment in mesechet:
            print(eachComment.uid())
            commentary = TextChunk(eachComment, 'he').as_string()
            trimmed_commentary = commentary.strip()
            if len(trimmed_commentary)>0:
                if trimmed_commentary[-1] != ':':
                    bad_tosafot.write(eachComment.uid() + '\r\n')
                if trimmed_commentary.count('-') > 1:
                    two_dash_tosafot.write(eachComment.uid() + '\r\n')
            else:
                tosafot_that_dont_exist.write(eachComment.uid() + '\r\n')

    tosafot_that_dont_exist.close()
    bad_tosafot.close()
    two_dash_tosafot.close()


collect_the_bad_tosafot()