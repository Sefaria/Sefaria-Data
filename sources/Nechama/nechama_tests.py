# -*- coding: utf-8 -*-

import django
django.setup()

from sefaria.client.wrapper import get_links
from sefaria.model import *
from research.source_sheet_disambiguator.main import refine_ref_by_text
from sheets import *
from main import *


class Test_prallel_matcher():

    def test_matching(self):
        np = Nechama_Parser("Genesis", "Bereshit", mode='fast')
        ref = u'Haamek Davar on Genesis 4:17'
        comment = u" שהבין קין עתה רצון ה\\', שטוב להיות מרבה בצרכיו ולא לחיות כחיה ובהמה על ידי עבודת האדמה לבדה, אלא לבקש חיי אנושי בייחוד, על כן בנה לו עיר."
        # new_ref = refine_ref_by_text(ref, "", comment, 20, alwaysCheck=True, truncateSheet=False, daf_skips=2, rashi_skips=2, overall=2)
        matched = np.check_reduce_sources(comment, Ref(ref))
        new_ref = matched[0].a.ref
        assert new_ref == Ref(u'Haamek Davar on Genesis 4:17:3')

        comment = u''' והוא היה לוטש וחורש כל נחושת וברזל. יאמר, כי הוא היה מחדד וחורש כל מלאכת נחושת וברזל. וכמוהו (הושע י"ד ג\\') "כל תשא עוון וקח טוב".'''
        ref = u'Ramban on Genesis 4:22'
        matched = np.check_reduce_sources(comment, Ref(ref))
        new_ref = matched[0].a.ref
        assert new_ref == Ref(u'Ramban on Genesis 4:22:1')

        comment = u'''ויעש אלהים את־הרקיע ויבדל בין המים אשר מתחת לרקיע ובין המים אשר מעל לרקיע ויהי־כן'''
        ref = u'Genesis.1.7'
        matched = np.check_reduce_sources(comment, Ref(ref))
        assert matched[0].a.ref == Ref(u'Genesis.1.7')

        comment = u'''לא טקסט קשור'''
        ref = u'Genesis.1.7'
        matched = np.check_reduce_sources(comment, Ref(ref))
        assert matched == []

class Test_try_parallel_matcher(object):

    def test_haftarah(self):
        individual=102
        parser = Nechama_Parser("Genesis", "Noach", mode='fast')
        got_sheet = parser.bs4_reader(["html_all/{}.html".format(individual)])
        assert got_sheet["html_all/{}.html".format(102)].sources[33]['ref'] == u'Ibn Ezra on Genesis 9:4:1'


# class Test_parse_he_Data_Types(object):
#
#     def test_perek_pasuk(self):
#         assert Ref(u'בראשית פרק א פסוק ג') == Ref('Genesis 1:3')
#         assert Ref(u'שמות ד פסוקים ג-ו') == Ref('Exodus 4:3-6')
#         # assert Ref(u'שמות ד פסוק ג - פרק ו') == Ref('Exodus 4:3-6:30')
#         # assert Ref(u'שמות ד פסוק ג - פסוק ו') == Ref('Exodus 4:3-6')
#         # assert Ref(u'שמות פרק ד - פרק ה פסוק ו') == Ref('Exodus 4:1-5:6')

class Test_ref_term_catching(object):

    def test_mechilta_parasha(self):
        # print Section.get_term(u'מכילתא, בשלח י"ד כ"ח')
        assert True

class Test_snunit_catch(object):
    """
    know to read a tags like this http://kodesh.snunit.k12.il/i/tr/t2692.htm and parse them correctly to Refs in the
    Sefaria library
    """
    def test_snunit(self):
        ref = Section.exctract_pasuk_from_snunit('http://kodesh.snunit.k12.il/i/tr/t2692.htm')
        assert True