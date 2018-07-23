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
        new_ref = np.check_reduce_sources(comment, Ref(ref))
        assert new_ref[0].a.ref == Ref(u'Haamek Davar on Genesis 4:17:2')

