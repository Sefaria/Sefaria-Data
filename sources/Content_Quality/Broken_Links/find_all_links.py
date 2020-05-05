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
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--ref", help="ref")
    parser.add_argument("-d", "--delete_links", help="delete the bad links", action="store_true")
    parser.add_argument("-m", "--manual_links", help="Detect manual links that are bad", action="store_true")
    parser.add_argument("-a", "--auto_links", help="Detect automatically generated links that are bad", action="store_true")
    parser.add_argument("-e", "--check_text_exists", help="Also make sure there is actual text at the links", action="store_true")
    args = parser.parse_args()
    print(args)

    sections = 0
    segments = 0
    sections_generated_by = Counter()
    segments_generated_by = Counter()
    nones = Counter()
    # for book in library.get_indexes_in_category("Other"):
    #     print(book)
    broken_link_res = broken_links(query={"generated_by": "add_links_from_text"}, ref_or_query="query", auto_links=args.auto_links,
                                   manual_links=args.manual_links, delete_links=args.delete_links,
                                   check_text_exists=args.check_text_exists)
    for link in broken_link_res:
        print(link)
        msg = link.split("\t")[-1]
        refs = eval(link.split("\t")[0])
        which_ref_is_bad = int(msg.split()[1]) - 1
    #     bad_ref = refs[which_ref_is_bad]
    #     good_ref = refs[1-which_ref_is_bad]
    #     link = Link().load({"refs": [good_ref, bad_ref]})
    #     if not link:
    #         link = Link().load({"refs": [bad_ref, good_ref]})
    #     assert link
    #     if ":" not in good_ref:
    #         sections += 1
    #         generated_by = sections_generated_by
    #     else:
    #         segments += 1
    #         generated_by = segments_generated_by
    #     if link.generated_by is None:
    #         good_ref = " ".join(good_ref.split()[0:-1])
    #         bad_ref = " ".join(bad_ref.split()[0:-1])
    #         refs = sorted([good_ref, bad_ref])
    #         nones[str(refs)] += 1
    #     else:
    #         generated_by[link.generated_by] += 1
    #
    # print(segments_generated_by.most_common(30))
    # print("***")
    # print(sections_generated_by.most_common(30))
    # print("***")
    # print(nones.most_common(30))