# encoding=utf-8

import re
import pytest
from collections import namedtuple
from data_utilities.ParseUtil import Description, ParsedDocument, run_on_list, directed_run_on_list, ClashError


def test_run_on_list():
    reg = re.compile('^@')
    test_data = [
        '@', 'foo', 'bar', '@', 'one', 'two', '@', 'a', 'b'
    ]
    with_matches = run_on_list(reg.match)
    assert with_matches(test_data) == [
        ['@', 'foo', 'bar'],
        ['@', 'one', 'two'],
        ['@', 'a', 'b']
    ]
    skip_matches = run_on_list(reg.match, include_matches=False)
    assert skip_matches(test_data) == [
        ['foo', 'bar'],
        ['one', 'two'],
        ['a', 'b']
    ]
    test_data.pop(0)
    assert skip_matches(test_data) == [
        ['one', 'two'],
        ['a', 'b']
    ]


def test_directed_run_on_list():
    def ident(item):
        match = re.match('@(\d)', item)
        if match:
            return int(match.group(1))
        else:
            return False

    test_data = [
        'garbage', '@1', 'foo', 'bar', '@3', 'one', 'two', '@4', 'a', 'b'
    ]
    with_matches = directed_run_on_list(ident)
    assert with_matches(test_data) == [
        [],
        ['@1', 'foo', 'bar'],
        [],
        ['@3', 'one', 'two'],
        ['@4', 'a', 'b']
    ]

    skip_matches = directed_run_on_list(ident, include_matches=False)
    assert skip_matches(test_data) == [
        [],
        ['foo', 'bar'],
        [],
        ['one', 'two'],
        ['a', 'b']
    ]

    one_indexed = directed_run_on_list(ident, include_matches=False, one_indexed=True)
    assert one_indexed(test_data) == [
        ['foo', 'bar'],
        [],
        ['one', 'two'],
        ['a', 'b']
    ]

    with_matches_one_indexed = directed_run_on_list(ident, True, True)  # probably not necessary, but why not?
    assert with_matches_one_indexed(test_data) == [
        ['@1', 'foo', 'bar'],
        [],
        ['@3', 'one', 'two'],
        ['@4', 'a', 'b']
    ]

    test_data[4] = '@1'
    with pytest.raises(ClashError):
        with_matches(test_data)


DocRow = namedtuple('DocRow', ['Chapter', 'Paragraph', 'text1', 'text2'])
my_doc = [
    DocRow(1, 1, 'a', 'one'),
    DocRow(1, 1, 'b', 'two'),
    DocRow(1, 2, 'c', 'three'),
    DocRow(2, 1, 'd', 'four'),
    DocRow(3, 1, 'e', 'five')
]


class ChapBuilder(object):
    def __init__(self):
        self.num = 0

    def __call__(self, row):
        if row.Chapter > self.num:
            self.num = row.Chapter
            return self.num
        else:
            return False

    def reset(self):
        self.num = 0


class ParagraphBuilder(object):
    def __init__(self):
        self.num = 0

    def __call__(self, row):
        if row.Paragraph > self.num:
            self.num = row.Paragraph
            return self.num
        else:
            return False

    def reset(self):
        self.num = 0


chap_builder = ChapBuilder()
paragraph_builder = ParagraphBuilder()

elements = [
    Description('Chapter', directed_run_on_list(chap_builder, one_indexed=True, start_method=chap_builder.reset)),
    Description('Paragraph',
                directed_run_on_list(paragraph_builder, one_indexed=True, start_method=paragraph_builder.reset)),
    Description('Line', lambda x: x)
]


def test_get_ja():
    parser = ParsedDocument('random', u'סתם', elements)
    parser.parse_document(my_doc)
    assert parser.get_ja() == [
        [[DocRow(1, 1, 'a', 'one'), DocRow(1, 1, 'b', 'two')], [DocRow(1, 2, 'c', 'three')]],
        [[DocRow(2, 1, 'd', 'four')]],
        [[DocRow(3, 1, 'e', 'five')]]
    ]


def test_filter_ja():
    parser = ParsedDocument('random', u'סתם', elements)
    parser.parse_document(my_doc)
    assert parser.filter_ja(lambda x: x.text1) == [
        [['a', 'b'], ['c']],
        [['d']],
        [['e']]
    ]


def test_multiple_parsers():
    # We want to create a situation where two classes have the same name but different attributes
    elements2 = elements[:]
    elements2[-1] = Description('Sentence', lambda x: [i.text1 for i in x])
    parser1 = ParsedDocument('random', u'סתם', elements)
    parser2 = ParsedDocument('random', u'סתם', elements2)

    parser1.parse_document(my_doc)
    parser2.parse_document(my_doc)

    assert parser1.get_ja() == [
        [[DocRow(1, 1, 'a', 'one'), DocRow(1, 1, 'b', 'two')], [DocRow(1, 2, 'c', 'three')]],
        [[DocRow(2, 1, 'd', 'four')]],
        [[DocRow(3, 1, 'e', 'five')]]
    ]

    assert parser2.get_ja() == [
        [['a', 'b'], ['c']],
        [['d']],
        [['e']]
    ]
