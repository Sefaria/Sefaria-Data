# encoding=utf-8

"""
Had to rewrite the parsing code to account for a new data format that was sent in by dicta
"""

import re
import sys
from functools import partial
from sefaria.utils.talmud import section_to_daf
from parse_nikkud import create_section, prettify_text
from data_utilities.ParseUtil import directed_run_on_list

import django
django.setup()
from sefaria.model import *


def identify_daf(book: str, daf_line: str) -> int:
    he_book = Ref(book).he_book()
    match = re.search(r'\u05d3\u05e3 [\u05d0-\u05ea]{1,3}[.:]', daf_line)
    if match:
        daf_data = match.group(0)
        return Ref(f'{he_book} {daf_data}').sections[0]
    else:
        return False


def prepare_file(filename):
    current_section, sections = [], []
    with open(filename) as fp:
        for line in fp:
            line = line.rstrip().lstrip()
            if re.search(r'^\*', line):  # start of new section
                if current_section:
                    sections.append(' '.join(current_section))
                    current_section = []
                sections.append(line)
            else:
                current_section.append(line)

        # final section
        if current_section:
            sections.append(' '.join(current_section))

    return sections


def parse_file(tractate):
    filename = f'{tractate}.txt'
    identify_daf_by_book = partial(identify_daf, tractate)
    preparsed = prepare_file(filename)
    parser = directed_run_on_list(identify_daf_by_book, include_matches=False, one_indexed=False)
    section_list = [item[0] if item else '' for item in parser(preparsed)]
    for section_index, section in enumerate(section_list):
        if not section:
            continue
        tref = f'{tractate} {section_to_daf(section_index)}'
        print(tref)
        dicta_vtitle = 'William Davidson Edition - Vocalized Aramaic'
        create_section(Ref(tref), section, dicta_vtitle)
        prettify_text(tref, dicta_vtitle)


if __name__ == '__main__':
    try:
        book_title = sys.argv[1]
    except IndexError:
        print("Please add name of Tractate")
        sys.exit(0)
    parse_file(book_title)
