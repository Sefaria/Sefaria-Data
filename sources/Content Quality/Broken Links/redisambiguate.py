# -*- coding: utf-8 -*-

import argparse
import django
django.setup()
from sefaria.model import *
from sefaria.clean import *
from sefaria.system.exceptions import InputError
from collections import *
import re
import csv
from research.link_disambiguator.main import *

pesachim_segments = {'Tosafot on Niddah': 17, 'Tosafot on Bekhorot': 12, 'Tosafot on Temurah': 4, 'Mefaresh on Tamid': 4, 'Rashi on Keritot': 3, 'Likutei Moharan': 3, 'Rashi on Meilah': 2, 'Tosafot on Meilah': 2, 'Rashi on Arakhin': 2, 'Rashi on Temurah': 2, 'Tosafot Yeshanim on Keritot': 2, 'Tosafot on Arakhin': 2, 'Shenei Luchot HaBerit, Torah Shebikhtav, Bo, Derekh Chayim': 1, 'Kessef Mishneh on Mishneh Torah, Sabbath': 1, 'Rashi on Niddah': 1}
found = {}

def redisambiguate(valid_ref, invalid_ref):
    invalid_ref_section = invalid_ref.top_section_ref()
    ld = Link_Disambiguator()
    results = ld.disambiguate_segment_by_snippet(valid_ref.normal(), [invalid_ref_section.normal()], with_match_text=True)
    if results[invalid_ref_section.normal()]:
        score = results[invalid_ref_section.normal()]["Score"]
        new_ref = results[invalid_ref_section.normal()]["B Ref"]
        already_exists = Link().load({"refs": [new_ref, valid_ref.normal()]}) or Link().load({"refs": [valid_ref.normal(), new_ref]})
        same_as_before = new_ref == invalid_ref.normal()
        # if already_exists or same_as_before:
        #     print("JUST DELETE")
        # else:
        #     print("DELETE AND CREATE")
        # print(score)
        valid_ref = valid_ref.normal()
        starts_with_pesachim = new_ref.startswith("Pesachim") or valid_ref.startswith("Pesachim")
        if starts_with_pesachim:
            print(new_ref) if valid_ref.startswith("Pesachim") else print(valid_ref)

if __name__ == "__main__":
    with open("segment_to_disambiguated.csv", 'r') as f:
        for row in csv.reader(f):
            ref1, ref2 = row
            ref1 = Ref(ref1)
            ref2 = Ref(ref2)
            ref1_empty = ref1.is_empty()
            ref2_empty = ref2.is_empty()
            if ref2_empty:
                redisambiguate(ref1, ref2)
            elif ref1_empty:
                redisambiguate(ref2, ref1)
