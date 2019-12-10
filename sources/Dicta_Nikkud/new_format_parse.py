# encoding=utf-8

"""
Had to rewrite the parsing code to account for a new data format that was sent in by dicta
"""

import re
import codecs
import argparse
from sefaria.utils.talmud import section_to_daf
from parse_nikkud import create_section, prettify_text
from data_utilities.ParseUtil import directed_run_on_list

import django
django.setup()
from sefaria.model import *


def identify_daf(daf_line):
    """
    :param unicode daf_line:
    :return: int
    """
    match = re.search(ur'\u05d3\u05e3 [\u05d0-\u05ea]{1,3}[.:]', daf_line)
    if match:
        daf_data = match.group(0)
        return Ref(u'{} {}'.format(u'ברכות', daf_data)).sections[0]
    else:
        return False


def prepare_file(filename):
    current_section, sections = [], []
    with codecs.open(filename, 'r', 'utf-8') as fp:
        for line in fp:
            line = line.rstrip()
            if re.search(ur'^\*', line):  # start of new section
                if current_section:
                    sections.append(u' '.join(current_section))
                    current_section = []
                sections.append(line)
            else:
                current_section.append(line)

        # final section
        if current_section:
            sections.append(u' '.join(current_section))

    return sections


def parse_file(filename):
    preparsed = prepare_file(filename)
    parser = directed_run_on_list(identify_daf, include_matches=False, one_indexed=False)
    section_list = [item[0] if item else u'' for item in parser(preparsed)]
    for section_index, section in enumerate(section_list):
        if not section:
            continue
        tref = u'Berakhot {}'.format(section_to_daf(section_index))
        print tref
        dicta_vtitle = 'William Davidson Edition - Vocalized Aramaic2'
        create_section(Ref(tref), section, dicta_vtitle)
        prettify_text(tref, dicta_vtitle)



parse_file('Berakhot.txt')
