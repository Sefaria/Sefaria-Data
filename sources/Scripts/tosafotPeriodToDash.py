# -*- coding: utf-8 -*-
import codecs

import regex

from sefaria.model import *
from sources.functions import post_text

"""
TODO:
1. Pull all Tosafot References from Shaas
2. Convert each Tosafot to a String
3. Change all em-dashes and en-dashed to dashes
4. Replace the period with a dash
5. Replace necessary colons with a dash
6. upload them using the API

.count of period should not be equal to the number of groups with a period
.count of colon should be 2 greater than groups

first run a method only selecting those tosafot
then, run the remaining Tosafot through a changer

"""


def standardize_tosafot_divrei_hamatchil_to_dash():
    tosafot_references = get_commentator_reference_collection("Tosafot")
    after_the_first_trim = remove_comments_every_period_and_colon_is_amud_marker(tosafot_references)
    the_second_coming = make_the_switches(after_the_first_trim)
    replace_the_texts_via_api(the_second_coming)


def get_commentator_reference_collection(commentator):
        all_refs = []
    #for mesechet in library.get_indexes_in_category('Bavli'):
        mesechet = 'Shevuot'
        all_refs.append(library.get_index(get_reference_name(commentator, mesechet)).all_segment_refs())
        return all_refs


def get_reference_name(commentator, mesechet):
    return "{} on {}".format(commentator, mesechet)


def remove_comments_every_period_and_colon_is_amud_marker(tosafot_references):
    periods = regex.compile('\(.{,8}\..{,8}\)')
    colons = regex.compile('\(.{,8}:.{,8}\)')
    after_the_first_trim = []
    for mesechet in tosafot_references:
        for eachComment in mesechet:
            commentary = TextChunk(eachComment, 'he').as_string()
            number_of_periods_in_parentheses = len(periods.findall(commentary))
            number_of_colons_in_parentheses = len(colons.findall(commentary))
            if commentary.count('.') > number_of_periods_in_parentheses or commentary.count(':') > (
                        number_of_colons_in_parentheses + 1):
                commentary = commentary.replace(u'\u2013', u'-').replace(u'\u2014', u'-')
                after_the_first_trim.append({'ref': eachComment, 'comment': commentary})
    return after_the_first_trim



def make_the_switches(list_of_dicts):
    changed_tosafots = []
    badTosafot = open('badTosafot.txt', 'w')
    for comment in list_of_dicts:
        commentary = comment['comment']
        the_first_dash = commentary.find('-')
        the_first_period = commentary.find('.')
        the_first_colon = commentary.find(':')
        if commentary[-1] != ':':
            badTosafot.write(comment['ref'].uid() + '\r\n')
        elif tester(commentary, the_first_dash, the_first_period):
            commentary = commentary.replace('.', ' -', 1)
            changed_tosafots.append({'ref': comment['ref'].uid(), 'comment': create_texts(commentary, comment['ref'])})
        # elif tester(commentary, the_first_dash, the_first_colon):
        #     commentary = commentary.replace(':', ' -', 1)
        #     changed_tosafots.append({'ref': comment['ref'].uid(), 'comment': create_texts(commentary, comment['ref'])})
    badTosafot.close()
    return changed_tosafots


def tester(commentary, the_first_dash, the_changeable_punctuation):
    return (the_changeable_punctuation != -1 and the_changeable_punctuation < 150 and commentary[the_changeable_punctuation + 1] != ')' and
            (the_changeable_punctuation < the_first_dash or the_first_dash == -1) and (the_first_dash > 150 or the_first_dash == -1) and
            (the_changeable_punctuation+1) != len(commentary))


def create_texts(commentary, reference):
    return {
        "versionTitle": reference.version_list()[0]["versionTitle"],
        "versionSource": reference.version_list()[0]["versionSource"],
        "language": "he",
        "text": commentary
    }


def replace_the_texts_via_api(list_of_fixed_tosafot):
    for eachTosafot in list_of_fixed_tosafot:
        print(eachTosafot['ref'])
        post_text(eachTosafot['ref'], eachTosafot['comment'])


standardize_tosafot_divrei_hamatchil_to_dash()
