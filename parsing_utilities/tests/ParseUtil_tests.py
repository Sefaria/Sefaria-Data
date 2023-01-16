# encoding=utf-8

import re
import pytest
from collections import namedtuple
# from data_utilities.ParseUtil import Description, ParsedDocument, run_on_list, directed_run_on_list, ClashError
from data_utilities.ParseUtil import *


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
    DocRow(2, 3, 'd', 'four'),
    DocRow(4, 1, 'e', 'five')
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


class AltParagraphBuilder(object):
    def __init__(self, tracker):
        self.tracker = tracker
        self.num = 0
        self.cur_chapter = 0

    def __call__(self, row):
        actual_chap = self.get_chap_number()
        if actual_chap != self.cur_chapter:
            self.cur_chapter = actual_chap
            self.num = 0
        if self.cur_chapter == 2:
            assert row.text1 == 'd'
        if row.Paragraph > self.num:
            self.num = row.Paragraph
            return self.num
        else:
            return False

    def get_chap_number(self):
        return self.tracker.get_ref('Chapter', one_indexed=True)


chap_builder = ChapBuilder()
paragraph_builder = ParagraphBuilder()

elements = [
    Description('Chapter', directed_run_on_list(chap_builder, one_indexed=True, start_method=chap_builder.reset)),
    Description('Paragraph',
                directed_run_on_list(paragraph_builder, one_indexed=True, start_method=paragraph_builder.reset)),
    Description('Line', lambda x: x)
]


def test_get_ja():
    parser = ParsedDocument('random', 'סתם', elements)
    parser.parse_document(my_doc)
    my_ja = parser.get_ja()
    assert my_ja == [
        [[DocRow(1, 1, 'a', 'one'), DocRow(1, 1, 'b', 'two')], [DocRow(1, 2, 'c', 'three')]],
        [[], [], [DocRow(2, 3, 'd', 'four')]],
        [],
        [[DocRow(4, 1, 'e', 'five')]]
    ]


def test_filter_ja():
    parser = ParsedDocument('random', 'סתם', elements)
    parser.parse_document(my_doc)
    assert parser.filter_ja(lambda x: x.text1) == [
        [['a', 'b'], ['c']],
        [[], [], ['d']],
        [],
        [['e']]
    ]


def test_multiple_parsers():
    # We want to create a situation where two classes have the same name but different attributes
    elements2 = elements[:]
    elements2[-1] = Description('Sentence', lambda x: [i.text1 for i in x])
    parser1 = ParsedDocument('random', 'סתם', elements)
    parser2 = ParsedDocument('random', 'סתם', elements2)

    parser1.parse_document(my_doc)
    parser2.parse_document(my_doc)

    assert parser1.get_ja() == [
        [[DocRow(1, 1, 'a', 'one'), DocRow(1, 1, 'b', 'two')], [DocRow(1, 2, 'c', 'three')]],
        [[], [], [DocRow(2, 3, 'd', 'four')]],
        [],
        [[DocRow(4, 1, 'e', 'five')]]
    ]

    assert parser2.get_ja() == [
        [['a', 'b'], ['c']],
        [[], [], ['d']],
        [],
        [['e']]
    ]


def test_get_ja_node():
    parser = ParsedDocument('random', 'סתם', elements)
    p_ja_node = parser.get_ja_node()

    m_ja_node = JaggedArrayNode()
    m_ja_node.add_primary_titles('random', 'סתם')
    m_ja_node.add_structure(['Chapter', 'Paragraph', 'Line'])

    assert p_ja_node.serialize() == m_ja_node.serialize()


def test_parse_state():
    parse_state = ParseState()
    alt_paragraph_builder = AltParagraphBuilder(parse_state)
    alt_elements = elements[:]
    alt_elements[1] = Description('Paragraph', directed_run_on_list(alt_paragraph_builder, one_indexed=True))
    parser = ParsedDocument('random', 'סתם', alt_elements)
    parser.attach_state_tracker(parse_state)
    parser.parse_document(my_doc)

    assert parser.filter_ja(lambda x: x.text1) == [
        [['a', 'b'], ['c']],
        [[], [], ['d']],
        [],
        [['e']]
    ]


def test_state_on_filter():
    def get_and_check(x, state):
        assert isinstance(state, ParseState)
        chap = state.get_ref('Chapter', one_indexed=True)
        par = state.get_ref('Paragraph', one_indexed=True)
        line = state.get_ref('Line', one_indexed=True)
        if (chap, par, line) == (2, 3, 1):
            assert x.text2 == 'four'
        else:
            assert x.text2 != 'four'
        return x.text2

    parse_state = ParseState()
    parser = ParsedDocument('random', 'סתם', elements)
    parser.attach_state_tracker(parse_state)
    parser.parse_document(my_doc)

    assert parser.filter_ja(get_and_check, parse_state) == [
        [['one', 'two'], ['three']],
        [[], [], ['four']],
        [],
        [['five']]
    ]
