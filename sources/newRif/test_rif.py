from RefactorRawFiles import *

def test_parse_pages_trivial():
    result = parse_pages(['@20 foo bar', '@20baz boo'])
    assert result == ['foo bar', 'baz boo']

def test_parse_pages_with_ch_tag():
    result = parse_pages(['@00chapter eleven \n@20 foo bar @20baz boo'])
    assert result == ['@00chapter eleven \n foo bar', 'baz boo']

def test_parse_paragraphs_trivial():
    result = parse_paragraphs('foo. bar: baz\n boo')
    assert result == ['foo.', 'bar:', 'baz', 'boo']

def test_parse_paragraphs_with_notes():
    result = parse_paragraphs('foo @13brakhot 12.@77 bar: @14shabbat 1: @77baz')
    assert result == ['foo @13brakhot 12.@77 bar:', '@14shabbat 1: @77baz']
