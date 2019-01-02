# -*- coding: utf-8 -*-

import django
django.setup()
import pytest
from django.urls import *
from django.core import urlresolvers


from parse_aspaklaria import *


class Test_Source_methods(object):

    global source
    source = Source(u'...והאודם מן האשה שממנו העור והבשר והדם, והרוח והנפש והנשמה משל הקב"ה ושלשתן שותפין בו. (כלאים לט א)', u'לקח טוב')

    # @classmethod
    # def setup_module(module):
    #     source = Source(u'...והאודם מן האשה שממנו העור והבשר והדם, והרוח והנפש והנשמה משל הקב"ה ושלשתן שותפין בו. (כלאים לט א)', u'לקח טוב')

    def test_index(self):
        # global parser
        # parser = Parser()
        # source = Source(u'...והאודם מן האשה שממנו העור והבשר והדם, והרוח והנפש והנשמה משל הקב"ה ושלשתן שותפין בו. (כלאים לט א)', u'לקח טוב')
        # source.extract_indx() # it is called inside the Source init
        assert True

    def test_get_ref_step2(self):
        # source = Source(u'טקסט (דרך חיים א ה)', u'מהר"ל')
        # assert source.ref == Ref(u'Derech Chaim 1.5')
        # source = Source(u'טקסט (בראשית כז ג)', u'מדרש רבה')
        # assert source.ref == Ref(u'Bereishit Rabbah 27:3')
        # source = Source(u'(רמב"ן, בראשית יח יא)', u'רמב"ן')
        # assert source.ref == Ref(u'Ramban on Genesis 18:11')
        source = Source(u'(משלי פרק א, תתקכט)', u'ילקוט שמועני')
        assert source.ref == Ref(u'Yalkut Shimoni on Nach 929.1')

    # def test_get_look_here_titles(self):
    #     look_here = [u'Bereishit Rabbah', u'Shemot Rabbah', u'Vayikra Rabbah', u'Bemidbar Rabbah', u'Devarim Rabbah', u'Esther Rabbah', u'Shir HaShirim Rabbah', u'Kohelet Rabbah', u'Ruth Rabbah', u'Eichah Rabbah']
    #     assert source.get_look_here_titles(look_here) == [(u'Bereishit Rabbah', u'Bereishit') ,(u'Shemot Rabbah', u'Shemot'), (u'Vayikra Rabbah', u'Vayikra'), (u'Bemidbar Rabbah', u'Bemidbar'), (u'Devarim Rabbah', u'Devarim'), (u'Esther Rabbah', u'Esther'), (u'Shir HaShirim Rabbah', u'Shir HaShirim'), (u'Kohelet Rabbah', u'Kohelet'), (u'Ruth Rabbah', u'Ruth'), (u'Eichah Rabbah', u'Eichah')]
