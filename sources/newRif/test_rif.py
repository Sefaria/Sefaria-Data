from RefactorRawFiles import *
from rif_utils import *

def test_parse_pages_trivial():
    result = parse_pages([['@20 foo bar', '@20baz boo'], 'Berakhot'])
    assert result == [['foo bar', True, 'Berakhot'], ['baz boo', False, 'Berakhot']]

def test_parse_pages_with_ch_tag():
    result = parse_pages([['@00chapter eleven \n@20 foo bar @20baz boo'], 'Berakhot'])
    assert result == [['@00chapter eleven \n foo bar', True, 'Berakhot'], ['baz boo', False, 'Berakhot']]

def test_parse_pages_with_colon():
    result = parse_pages([['foobar:@20 foo bar @20baz boo'], 'Berakhot'])
    assert result == [['foobar:', True, 'Berakhot'], ['foo bar', True, 'Berakhot'], ['baz boo', False, 'Berakhot']]

def test_netlen():
    result = netlen('פו בר בז ברוז פובר בזבר.')
    assert result == 6

def test_parse_paragraphs_trivial():
    result = parse_paragraphs(['בז ברוז פובר בזבר: פו בר בז ברוז פובר בזבר. פו בר בז ברוז פובר בזבר\n בר בז ברוז פובר בזבבר. גל', True, 'Berakhot'])
    assert result == ['בז ברוז פובר בזבר: פו בר בז ברוז פובר בזבר.', 'פו בר בז ברוז פובר בזבר', 'בר בז ברוז פובר בזבבר. גל']

def test_parse_paragraphs_trivial_false():
    result = parse_paragraphs(['בז ברוז פובר בזבר: פו בר בז ברוז פובר בזבר. פו בר בז ברוז פובר בזבר\n בר בז ברוז פובר בזבבר. גל', False, 'Berakhot'])
    assert result == ['בז ברוז פובר בזבר:', 'פו בר בז ברוז פובר בזבר.', 'פו בר בז ברוז פובר בזבר', 'בר בז ברוז פובר בזבבר. גל']

def test_parse_paragraphs_with_notes():
    result = parse_paragraphs(['foo @13brakhot 12.@77 bar: @14shabbat 1: @77baz', False, 'Berakhot'])
    assert result == ['foo @13brakhot 12.@77 bar:', '@14shabbat 1: @77baz']

def test_parse_paragraphs_with_suspect():
    result = parse_paragraphs(['foo @13brakhot 12. baz', False, 'Berakhot'])
    assert result == ['foo @13brakhot 12.@$', 'baz']

def test_parse_paragraphs_with_end():
    result = parse_paragraphs(['foo @13brakhot 12.@77 bar: baz.', False, 'Berakhot'])
    assert result == ['foo @13brakhot 12.@77 bar:', 'baz.']
