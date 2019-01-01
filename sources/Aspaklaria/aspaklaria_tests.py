# -*- coding: utf-8 -*-

import django
django.setup()
import pytest


from parse_aspaklaria import *


class Test_index_catching(object):

    # parser=None

    # @classmethod
    # def setup_module(module):
    #     parser = Parser()

    def test_index(self):
        # global parser
        # parser = Parser()
        source = Source(u'...והאודם מן האשה שממנו העור והבשר והדם, והרוח והנפש והנשמה משל הקב"ה ושלשתן שותפין בו. (כלאים לט א)', u'לקח טוב')
        # source.extract_indx() # it is called inside the Source init
        assert True
