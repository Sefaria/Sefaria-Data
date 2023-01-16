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
from linking_utilities.citation_disambiguator.citation_disambiguator import *

pesachim_segments = {'Tosafot on Niddah': 17, 'Tosafot on Bekhorot': 12, 'Tosafot on Temurah': 4, 'Mefaresh on Tamid': 4, 'Rashi on Keritot': 3, 'Likutei Moharan': 3, 'Rashi on Meilah': 2, 'Tosafot on Meilah': 2, 'Rashi on Arakhin': 2, 'Rashi on Temurah': 2, 'Tosafot Yeshanim on Keritot': 2, 'Tosafot on Arakhin': 2, 'Shenei Luchot HaBerit, Torah Shebikhtav, Bo, Derekh Chayim': 1, 'Kessef Mishneh on Mishneh Torah, Sabbath': 1, 'Rashi on Niddah': 1}
found = {}

def redisambiguate(valid_ref, invalid_ref):
    result = {"delete": None, "create": None}
    msg = "disambiguator found no match"

    invalid_ref_section = invalid_ref.top_section_ref()
    ld = CitationDisambiguator()
    results = ld.disambiguate_segment_by_snippet(valid_ref.normal(), [invalid_ref_section.normal()], with_match_text=True)
    if results[invalid_ref_section.normal()]:
        new_ref = results[invalid_ref_section.normal()]["B Ref"]
        already_exists = Link().load({"$and": [{"refs": new_ref}, {"refs": valid_ref.normal()}]})
        same_as_before = new_ref == invalid_ref.normal()
        if not same_as_before and not already_exists:
            result["create"] = [new_ref, valid_ref.normal()]
            msg = "disambiguator found a better match"
        elif same_as_before:
            assert invalid_ref.is_empty()
            msg = "disambiguator found same match as before but {} is empty".format(invalid_ref.normal())

    result["delete"] = [invalid_ref.normal(), valid_ref.normal(), msg]
    return result


if __name__ == "__main__":
    with open("segment_to_disambiguated.csv", 'r') as f:
        for row in csv.reader(f):
            ref1, ref2 = row
            ref1 = Ref(ref1)
            ref2 = Ref(ref2)
            ref1_empty = ref1.is_empty()
            ref2_empty = ref2.is_empty()
            if ref2_empty:
                result = redisambiguate(ref1, ref2)
            elif ref1_empty:
                result = redisambiguate(ref2, ref1)
