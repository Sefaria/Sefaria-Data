# -*- coding: utf-8 -*-

import django
django.setup()

from sefaria.client.wrapper import get_links
from sefaria.model import *
from research.source_sheet_disambiguator.main import refine_ref_by_text
from sheets import *
from parse_sheets import *


class Test_prallel_matcher():

    def test_matching(self):
        np = Nechama_parser()
        ref = u'Haamek Davar on Genesis 4:17'
        comment = u" שהבין קין עתה רצון ה\\', שטוב להיות מרבה בצרכיו ולא לחיות כחיה ובהמה על ידי עבודת האדמה לבדה, אלא לבקש חיי אנושי בייחוד, על כן בנה לו עיר."
        # new_ref = refine_ref_by_text(ref, "", comment, 20, alwaysCheck=True, truncateSheet=False, daf_skips=2, rashi_skips=2, overall=2)
        matched = np.check_reduce_sources(comment, Ref(ref))
        new_ref = matched[0].a.ref
        assert new_ref == Ref(u'Haamek Davar on Genesis 4:17:2')

        comment = u''' והוא היה לוטש וחורש כל נחושת וברזל. יאמר, כי הוא היה מחדד וחורש כל מלאכת נחושת וברזל. וכמוהו (הושע י"ד ג\\') "כל תשא עוון וקח טוב".'''
        ref = u'Ramban on Genesis 4:22'
        matched = np.check_reduce_sources(comment, Ref(ref))
        # new_ref = matched[0].a.ref
        # assert new_ref == Ref(u'Ramban on Genesis 4:22:1')

        comment = u'''ונקרא כך שנתערבו בו הצורות ובקר הפך ערב שיוכל אדם לבקר '''
        ref = u'Ibn Ezra on Genesis.1.5'
        matched = np.check_reduce_sources(comment, Ref(ref))
        new_ref = matched[0].a.ref == Ref(u'Ibn Ezra on Genesis.1.5.2')