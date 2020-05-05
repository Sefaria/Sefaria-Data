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

    count_per_book_A = Counter()
    count_per_book_B = Counter()
    # for ref in ["Rashi on Pesachim", "Tosafot on Pesachim"]:

    ref = "Pesachim"
    query = {"generated_by": "link_disambiguator", "refs": {"$regex": "Pesachim"}}
    broken_link_res = broken_links(tref=ref, ref_or_query="ref", auto_links=args.auto_links,
                                   manual_links=args.manual_links, delete_links=args.delete_links,
                                   check_text_exists=args.check_text_exists)
    for link in broken_link_res:
        book = ""
        refs = eval(link.split("\t")[0])
        if refs[1].startswith("Pesachim") and "Pesachim" in refs[0]:
            comm_link = 0
        elif refs[0].startswith("Pesachim") and "Pesachim" in refs[1]:
            comm_link = 1
        else:
            for ref in refs:
                try:
                    poss_book = Ref(ref).book
                    if poss_book != "Pesachim":
                        assert not book
                        book = poss_book
                    else:
                        if ":" in ref:
                            relevant_dict = count_per_book_A
                            print(link)
                        else:
                            relevant_dict = count_per_book_B
                except InputError:
                    continue
            relevant_dict[book] += 1
        #
        # if "has no text" in link[2]:
        #     which_has_no_text = int(re.search("Ref (\d)", link[2]).group(1)) - 1
        #     if comm_link != which_has_no_text:
        #         print(link)



    print("\nSegmented")
    for tuple in count_per_book_A.most_common(15):
        print(tuple)
    print("\nUnsegmented")
    for tuple in count_per_book_B.most_common(15):
        print(tuple)
