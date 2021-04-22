# encoding=utf-8

import re
import os
import codecs
import pytest
from io import StringIO
from data_utilities import util

import django
django.setup()
from sefaria.model import *


class Test_WeightedLevenshtein:

    @classmethod
    def setup_class(cls):
        cls.instance = util.WeightedLevenshtein()

    def test_exact_match(self):
        assert self.instance.calculate('שלום עולם', 'שלום עולם') == 100

    def test_biggest_difference(self):
        assert self.instance.calculate('שלום', 'צצצצצ') == 0

    def test_sofit(self):
        assert self.instance.calculate('שלומ', 'שלום') == 100

    def test_nothing(self):
        with pytest.raises(util.LevenshteinError):
            self.instance.calculate('', '')


def test_get_gematria():
    assert util.getGematria('א') == 1
    assert util.getGematria('תשעב') == 772


def test_he_ord():
    assert util.he_ord('ו') == 6
    assert util.he_ord('ש') == 21


def test_he_num_to_char():
    assert util.he_num_to_char(5) == 'ה'
    assert util.he_num_to_char(16) == 'ע'
    with pytest.raises(AssertionError):
        util.he_num_to_char(23)


def test_num_to_heb():
    assert util.numToHeb(16) == 'טז'
    assert util.numToHeb(962) == 'תתקסב'


def test_jagged_array_to_xml():
    xml_buffer = StringIO()
    util.ja_to_xml(['foo'], ['foo'], xml_buffer)
    xml_buffer.seek(0)
    assert xml_buffer.read() == '<root><foo index="1">foo</foo></root>'

    with pytest.raises(TypeError):
        util.ja_to_xml(['foo', {'bar'}], ['foo'], xml_buffer)
    xml_buffer.close()


def test_clean_jagged_array():
    dirty_ja = [['foo&', 'bar&'], ['hello&', 'world&']]
    clean_ja = [['foo', 'bar'], ['hello', 'world']]
    result = util.clean_jagged_array(dirty_ja, ['&'])
    assert result == clean_ja
    assert result != dirty_ja


def test_traverse_ja():
    test_ja = [['foo', 'bar'], ['hello', 'world']]
    explicit_data = [
        {'data': 'foo', 'indices': [0, 0]},
        {'data': 'bar', 'indices': [0, 1]},
        {'data': 'hello', 'indices': [1, 0]},
        {'data': 'world', 'indices': [1, 1]}
    ]
    for test_item, explicit_item in zip(util.traverse_ja(test_ja), explicit_data):
        assert test_item == explicit_item


def test_convert_dict_to_array():
    my_dict = {
        1: 'foo',
        3: 'bar',
        5: 'baz'
    }
    assert util.convert_dict_to_array(my_dict, str) == ['', 'foo', '', 'bar', '', 'baz']


def test_singleton():
    class FakeDict(dict, metaclass=util.Singleton):
        pass

    foo, bar = FakeDict(), FakeDict()
    assert id(foo) == id(bar)


def test_clean_whitespace():
    assert util.clean_whitespace('  foo   bar   ') == 'foo bar'


def test_split_version():
    single_version = {
        'versionTitle': 'test version',
        'text': [
            ['foo', 'bar'],
            ['hello', 'world']
        ]
    }
    split_versions = util.split_version(single_version, 2)
    assert len(split_versions) == 2
    assert split_versions[0]['versionTitle'] == 'test version, Vol 1'
    assert split_versions[1]['versionTitle'] == 'test version, Vol 2'
    assert len(split_versions[0]['text']) == 2
    assert split_versions[0]['text'] == [['foo', 'bar'], []]
    assert split_versions[1]['text'] == [[], ['hello', 'world']]


def test_split_list():
    stuff = list(range(12))
    split_stuff = list(util.split_list(stuff, 3))
    assert len(split_stuff) == 3
    assert split_stuff[0] == [0, 1, 2, 3]
    assert split_stuff[1] == [4, 5, 6, 7]
    assert split_stuff[2] == [8, 9, 10, 11]


def test_schema_with_default():
    ja = JaggedArrayNode()
    ja.add_primary_titles('foo', 'פו')
    ja.add_structure(['Word'])
    d = util.schema_with_default(ja)

    assert d.serialize() == {
        'key': 'foo',
        'nodes': [
            {
                'addressTypes': ['Integer'],
                'default': True,
                'depth': 1,
                'key': 'default',
                'nodeType': 'JaggedArrayNode',
                'sectionNames': ['Word']
            }
        ],
        'titles': [
            {'lang': 'en', 'primary': True, 'text': 'foo'},
            {'lang': 'he', 'primary': True, 'text': 'פו'}
        ]
    }


def test_placeholder():
    holder = util.PlaceHolder()
    assert holder(re.search(r'f', 'foo'))
    assert holder.group() == 'f'


def test_file_to_ja():
    data = StringIO('''@22\nfoo\nbar\n@22\nhello\nworld''')
    ja = util.file_to_ja(2, data, ['@22'], lambda x: [c.rstrip() for c in x])
    assert ja.array() == [
        ['foo', 'bar'],
        ['hello', 'world']
    ]


def test_file_to_ja_g():
    data = StringIO('''@22א\nfoo\nbar\n@22ג\nhello\nworld''')
    ja = util.file_to_ja_g(2, data, [r'@22(?P<gim>[\u05d0-\u05ea])'], lambda x: [c.rstrip() for c in x], True)
    assert ja.array() == [
        ['foo', 'bar'],
        [],
        ['hello', 'world']
    ]


def test_restructure_file():
    with codecs.open('test_file.txt', 'w', 'utf-8') as fp:
        fp.write('foo\nbar')
    util.restructure_file('test_file.txt', lambda x: '{}!\n'.format(x.rstrip()))
    with codecs.open('test_file.txt', 'r', 'utf-8') as fp:
        fixed = fp.read()

    assert fixed == 'foo!\nbar!\n'
    os.remove('test_file.txt')


class TestNormalizationMapping:
    def test_simple_case(self):
        text = "a###b##c"
        find_text_to_remove = lambda x: [(m, '') for m in re.finditer(r'#+', x)]
        rm = util.get_mapping_after_normalization(text, find_text_to_remove)
        assert rm == {1: 3, 2: 5}

    def test_with_substitution(self):
        text = "a###b##c"
        find_text_to_remove = lambda x: [(m, ' ') for m in re.finditer(r'#+', x)]
        rm = util.get_mapping_after_normalization(text, find_text_to_remove)
        assert rm == {1: 2, 3: 3}

    def test_real_case(self):
        norm_mention = "Rabbi Yehuda"
        norm_regex = r"\s*<[^>]+>\s*"
        text = """The priest <b>would bring an earthenware</b> drinking <b>vessel [<i>peyalei</i>] and he would pour into it half a <i>log</i> of water from the basin</b> in the Temple. <b>Rabbi Yehuda says:</b> The priest would pour only <b>a quarter</b>-<i>log</i> of water. <b>Just as</b> Rabbi Yehuda <b>minimizes the writing,</b> as he requires"""
        norm_text = re.sub(norm_regex, ' ', text)
        find_text_to_remove = lambda x: [(m, ' ') for m in re.finditer(norm_regex, x)]
        rm = util.get_mapping_after_normalization(text, find_text_to_remove)
        norm_inds = (222, 234)
        assert norm_text[norm_inds[0]:norm_inds[1]] == norm_mention

        # include_trailing_chars == False
        unnorm_s, unnorm_e = util.convert_normalized_indices_to_unnormalized_indices([norm_inds], rm)[0]
        assert text[unnorm_s:unnorm_e] == norm_mention
        assert re.sub(norm_regex, '', text[unnorm_s:unnorm_e]) == norm_mention

        # prefix
        unnorm_s, unnorm_e = util.convert_normalized_indices_to_unnormalized_indices([(norm_inds[0], norm_inds[0])], rm)[0]
        assert text[unnorm_s:unnorm_e] == ""

    def test_word_to_char(self):
        test_string = 'some words go here\n\nhello world'
        words = ['go', 'here', 'hello']
        word_indices = (2, 4)
        result = util.char_indices_from_word_indices(test_string, [word_indices])[0]
        start, end = result
        assert test_string[start:end] == 'go here\n\nhello'
        assert test_string[start:end].split() == words
