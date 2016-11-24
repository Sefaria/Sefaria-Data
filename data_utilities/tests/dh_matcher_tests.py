# -*- coding: utf-8 -*-
from data_utilities import dibur_hamatchil_matcher as dhm
import regex as re

class TestDHMatcherFunctions:

    def test_is_abbrev(self):
        iam = dhm.isAbbrevMatch
        def sp(string):
            return re.split(u'\s+',string)

        assert (True, 1, False) == iam(0,u'אל',sp(u'אמר ליה'),0)
        assert (True, 2, False) == iam(0,u'אעפ',sp(u'אף על פי'),0)
        assert (True, 1, False) == iam(0,u'בביכנ',sp(u'בבית כנסת'),0)
        assert (True, 4, False) == iam(0,u'aabbcde',sp(u'aa123 bb123 c123 d123 e123'),0)
        assert (True, 3, False) == iam(0,u'aaabbcd',sp(u'aaa123 bb123 c123 d123'),0)