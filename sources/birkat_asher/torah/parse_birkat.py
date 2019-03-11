# encoding=utf-8

from __future__ import unicode_literals, print_function
import re
import unicodecsv
from functools import partial
from data_utilities.util import getGematria
from data_utilities.ParseUtil import Description, ParsedDocument, directed_run_on_list

import django
django.setup()
from sefaria.model import *


"""
Start with testing. Make sure chapters ascend. Break into lists and make sure verses ascend. Convert to ParsedDocument
and make sure chapters/verses match base text.
"""


class StructureError(ValueError):
    pass


def get_structure_unit(column_index, base_marker, segment_row):
    poi = segment_row[column_index]
    if not poi:
        return False
    pattern = ''.join([base_marker, '([\u05d0-\u05ea]{1,3})'])
    match = re.match(pattern, poi)
    if not match:
        raise StructureError
    return getGematria(match.group(1))


def check_structure_markers(struct_method, doc_rows):
    issues = []
    for row_num, row in enumerate(doc_rows):
        try:
            struct_method(row)
        except StructureError:
            issues.append(row_num)
    return issues


def check_ascending(decode_method, doc_rows, verbose=False):
    indices = filter(None, [decode_method(r) for r in doc_rows])
    is_sorted = all(indices[i] < indices[i+1] for i in xrange(len(indices) - 1))

    if verbose:
        if is_sorted:
            print("No out of order issues found")
        else:
            print("Out of order")
            for i in xrange(len(indices) - 1):
                if indices[i] >= indices[i+1]:
                    print("{} appeared before {}".format(indices[i], indices[i+1]))

    return is_sorted


get_chapters = partial(get_structure_unit, 0, '@11')
get_verses = partial(get_structure_unit, 1, '@22')

"""
A builder class can be helpful. Takes file and book name.
1) Tests structure units
2) Checks ascending chapters
3) Splits into chapters
4) Checks ascending verses
5) Generates and returns a ParsedDocument
"""


class DocBuilder(object):
    def __init__(self, book_name):
        self.book = book_name
        self.filename = "Birkat_Asher_on_{}.tsv".format(self.book)
        self._chap_parse_method, self._verse_parse_method = None, None
        with open(self.filename, 'r') as fp:
            self.rows = list(unicodecsv.reader(fp, delimiter=str('\t')))

        self.valid_marks = self.check_for_bad_marks()
        self.in_order = self.check_ascending_on_book()
        if not self.in_order:
            print("Out of order in {}".format(self.book))
            self.check_ascending_on_book(verbose=True)

        print("")

    def check_for_bad_marks(self):
        def run_check(unit_checker, unit_type):
            issues = check_structure_markers(unit_checker, self.rows)
            if issues:
                print("Weird {} found in {}:".format(unit_type, self.book))
                for issue in issues:
                    print("Found in row {}".format(issue))
                return False

            else:
                print("No problems with {}s in {}".format(unit_type, self.book))
                return True

        chaps = run_check(get_chapters, 'chapter')
        verses = run_check(get_verses, 'verse')

        return chaps and verses

    def split_to_chapters(self, rows):
        if self._chap_parse_method is None:
            self._chap_parse_method = directed_run_on_list(get_chapters, one_indexed=True)
        return self._chap_parse_method(rows)

    def split_to_verses(self, rows):
        if self._verse_parse_method is None:
            self._verse_parse_method = directed_run_on_list(get_verses, one_indexed=True)
        return self._verse_parse_method(rows)

    def check_ascending_on_book(self, verbose=False):
        chaps_ascending = check_ascending(get_chapters, self.rows, verbose=verbose)
        chapters = self.split_to_chapters(self.rows)

        if not verbose:
            verses_ascending = all((check_ascending(get_verses, chap) for chap in chapters))

        else:
            verses_ascending = True
            for chap_num, chap in enumerate(chapters, 1):
                cur_test = check_ascending(get_verses, chap)
                if not cur_test:
                    print("Bad verse in chapter {}".format(chap_num))
                    verses_ascending = False

        return chaps_ascending and verses_ascending


[DocBuilder(b) for b in library.get_indexes_in_category("Torah")]

