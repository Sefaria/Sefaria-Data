from RefactorRawFiles import *
from rif_utils import *

def test_parse_pages_trivial():
    result = parse_pages(['@20 foo bar', '@20baz boo'])
    assert result == [{'page': 'foo bar', 'is_start_in_new_sec': True}, {'page': 'baz boo', 'is_start_in_new_sec': False}]

def test_parse_pages_with_ch_tag():
    result = parse_pages(['@00chapter one \n@20 foo bar @20baz boo'])
    assert result == [{'page': '@00chapter one \n foo bar', 'is_start_in_new_sec': True}, {'page': 'baz boo', 'is_start_in_new_sec': False}]

def test_parse_pages_with_colon():
    result = parse_pages(['foobar:@20 foo bar @20baz boo'])
    assert result == [{'page': 'foobar:', 'is_start_in_new_sec': True}, {'page': 'foo bar', 'is_start_in_new_sec': True}, {'page': 'baz boo', 'is_start_in_new_sec': False}]

def test_netlen():
    result = netlen('פו בר בז ברוז פובר בזבר.')
    assert result == 6

def test_parse_paragraphs_trivial():
    result = parse_paragraphs({'page': 'בז ברוז פובר בזבר: פו בר בז ברוז פובר בזבר. פו בר בז ברוז פובר בזבר\n בר בז ברוז פובר בזבבר. גל', 'is_start_in_new_sec': True})
    assert result == ['בז ברוז פובר בזבר: פו בר בז ברוז פובר בזבר.', 'פו בר בז ברוז פובר בזבר', 'בר בז ברוז פובר בזבבר. גל']

def test_parse_paragraphs_trivial_false():
    result = parse_paragraphs({'page': 'בז ברוז פובר בזבר: פו בר בז ברוז פובר בזבר. פו בר בז ברוז פובר בזבר\n בר בז ברוז פובר בזבבר. גל', 'is_start_in_new_sec': False})
    assert result == ['בז ברוז פובר בזבר:', 'פו בר בז ברוז פובר בזבר.', 'פו בר בז ברוז פובר בזבר', 'בר בז ברוז פובר בזבבר. גל']

def test_parse_paragraphs_with_notes():
    result = parse_paragraphs({'page': 'foo @13brakhot 12.@77 bar: @14shabbat 1: @77baz', 'is_start_in_new_sec': False})
    assert result == ['foo @13brakhot 12.@77 bar:', '@14shabbat 1: @77baz']

def test_parse_paragraphs_with_suspect():
    result = parse_paragraphs({'page': 'foo @13brakhot 12. baz', 'is_start_in_new_sec': False})
    assert result == ['foo @13brakhot 12.@$', 'baz']

def test_parse_paragraphs_with_end():
    result = parse_paragraphs({'page': 'foo @13brakhot 12.@77 bar: baz.', 'is_start_in_new_sec': False})
    assert result == ['foo @13brakhot 12.@77 bar:', 'baz.']
