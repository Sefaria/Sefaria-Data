# encoding=utf-8

import pytest
from StringIO import StringIO
from data_utilities import util


class Test_WeightedLevenshtein:

    @classmethod
    def setup_class(cls):
        cls.instance = util.WeightedLevenshtein()

    def test_exact_match(self):
        assert self.instance.calculate(u'שלום עולם', u'שלום עולם') == 100

    def test_biggest_difference(self):
        assert self.instance.calculate(u'שלום', u'צצצצצ') == 0

    def test_sofit(self):
        assert self.instance.calculate(u'שלומ', u'שלום') == 100

    def test_nothing(self):
        with pytest.raises(util.LevenshteinError):
            self.instance.calculate(u'', u'')


def test_get_gematria():
    assert util.getGematria(u'א') == 1
    assert util.getGematria(u'תשעב') == 772


def test_he_ord():
    assert util.he_ord(u'ו') == 6
    assert util.he_ord(u'ש') == 21


def test_he_num_to_char():
    assert util.he_num_to_char(5) == u'ה'
    assert util.he_num_to_char(16) == u'ע'
    with pytest.raises(AssertionError):
        util.he_num_to_char(23)


def test_num_to_heb():
    assert util.numToHeb(16) == u'טז'
    assert util.numToHeb(962) == u'תתקסב'


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
    test_ja = [[u'foo', u'bar'], [u'hello', u'world']]
    explicit_data = [
        {'data': u'foo', 'indices': [0, 0]},
        {'data': u'bar', 'indices': [0, 1]},
        {'data': u'hello', 'indices': [1, 0]},
        {'data': u'world', 'indices': [1, 1]}
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
    class FakeDict(dict):
        __metaclass__ = util.Singleton

    foo, bar = FakeDict(), FakeDict()
    assert id(foo) == id(bar)


def test_clean_whitespace():
    assert util.clean_whitespace(u'  foo   bar   ') == u'foo bar'


def test_split_version():
    pass


def test_split_list():
    pass


def test_schema_with_default():
    pass
