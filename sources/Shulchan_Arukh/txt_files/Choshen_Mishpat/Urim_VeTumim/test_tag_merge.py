# encoding=utf-8

import pytest
from tag_merge import merge_tags, HTMLMap


def test_self_merge():
    s = u'''Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''
    html_map = HTMLMap(s)
    assert html_map.merge_tags(html_map.stripped_string) == s


def test_tag_merge():
    s1 = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''
    s2 = u'''Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    result = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    assert merge_tags(s1, s2) == result


def test_end_word():
    s1 = u'''Lorem ipsum dolor sit amet, consectetur<i data-commentator="Ba'er Hetev" data-order="9"></i> adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''
    s2 = u'''Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    result = u'''Lorem ipsum dolor sit amet, consectetur<i data-commentator="Ba'er Hetev" data-order="9"></i> adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    assert merge_tags(s1, s2) == result


def test_mid_word():
    s1 = u'''Lorem ipsum dolor sit amet, (consectetur<i data-commentator="Ba'er Hetev" data-order="9"></i>) adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''
    s2 = u'''Lorem ipsum dolor sit amet, (consectetur) adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    result = u'''Lorem ipsum dolor sit amet, (consectetur<i data-commentator="Ba'er Hetev" data-order="9"></i>) adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    assert merge_tags(s1, s2) == result


def test_tag_clash():
    s1 = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''
    s2 = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Tumim" data-order="5"/></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    result1 = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i><i data-commentator="Tumim" data-order="5"/></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''
    result2 = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Tumim" data-order="5"/></i><i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    actual_result = merge_tags(s1, s2)
    assert actual_result == result1 or actual_result == result2


def test_words_dont_match():
    s1 = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''
    s2 = u'''Lorem ipsum dolor sit amet, sonsectetur adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    result = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    with pytest.raises(AssertionError):
        merge_tags(s1, s2)

    assert merge_tags(s1, s2, validate=False) == result


def test_tag_at_beginning():
    s1 = u'''<i data-commentator="Ba'er Hetev" data-order="9"></i>Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''
    s2 = u'''Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    result = u'''<i data-commentator="Ba'er Hetev" data-order="9"></i>Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    assert merge_tags(s1, s2) == result


def test_extra_character():
    s1 = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''
    s2 = u'''PLorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    result = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    assert merge_tags(s1, s2) == result


def test_missing_character():
    s1 = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''
    s2 = u'''Lorem isum dolor sit amet, consectetur adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    result = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    assert merge_tags(s1, s2) == result


def test_missing_char_mid_word():
    s1 = u'''Lorem ipsum dolor sit amet, (consectetur<i data-commentator="Ba'er Hetev" data-order="9"></i>) adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''
    s2 = u'''Lorem ipsm dolor sit amet, (consectetur) adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    result = u'''Lorem ipsum dolor sit amet, (consectetur<i data-commentator="Ba'er Hetev" data-order="9"></i>) adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    assert merge_tags(s1, s2) == result


def test_multiple_missing_and_added():
    s1 = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''
    s2 = u'''Lorem ipsum dolor sit amet consectetur adipiscing elit. Fusce eleifend interdum mauris, quis (tempus dolor). In eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    result = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    assert merge_tags(s1, s2) == result


def test_extra_word():
    s1 = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''
    s2 = u'''Lorem foo ipsum dolor sit amet, consectetur adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    result = u'''Lorem ipsum dolor sit amet, consectetur <i data-commentator="Ba'er Hetev" data-order="9"></i>adipiscing elit. Fusce eleifend interdum mauris, quis tempus dolor. In <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>eget dolor felis. Praesent vel <i data-commentator="Tumim" data-order="5"/></i>tortor dapibus, bibendum lacus id, ornare lacus. Proin commodo magna at gravida facilisis.'''

    with pytest.raises(AssertionError):
        assert merge_tags(s1, s2) == result

def test_hebrew():
    s1 = u'''<i data-commentator="Beur HaGra" data-order="20"></i><i data-commentator="Me'irat Einayim" data-order="9"></i><i data-commentator="Siftei Kohen" data-order="10"></i><i data-commentator="Be'er HaGolah" data-label="ט" data-order="10"></i>אע"פ שיחיד מומחה לרבים מותר לו לדון <i data-commentator="Ba'er Hetev" data-order="9"></i>יחידי מצות חכמים <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>שיושיב עמו אחרים:'''
    s2 = u'''אע"פ שיחיד מומחה לרבים מותר לו לדון יחידי <i data-commentator="Tumim" data-order="5"/></i>מצות חכמים שיושיב עמו אחרים:'''

    result = u'''<i data-commentator="Beur HaGra" data-order="20"></i><i data-commentator="Me'irat Einayim" data-order="9"></i><i data-commentator="Siftei Kohen" data-order="10"></i><i data-commentator="Be'er HaGolah" data-label="ט" data-order="10"></i>אע"פ שיחיד מומחה לרבים מותר לו לדון <i data-commentator="Ba'er Hetev" data-order="9"></i>יחידי <i data-commentator="Tumim" data-order="5"/></i>מצות חכמים <i data-commentator="Ketzot HaChoshen" data-order="4"></i><i data-commentator="Me'irat Einayim" data-order="10"></i><i data-commentator="Netivot HaMishpat, Hidushim" data-order="7"></i>שיושיב עמו אחרים:'''

    assert merge_tags(s1, s2) == result
