# encoding=utf-8

import pytest
from sources.EinMishpat import ein_parser

def test_fddaf():
    assert ein_parser.parse_em('test_file1.txt', 1, 'test_error.txt') == {}
    assert ein_parser.parse_em('test_file1.txt', 1, 'test_error.txt') == {}

    semag = ein_parser.Semag()
    # mass =
    # semag.parse_semag(u'עשין מה', mass)