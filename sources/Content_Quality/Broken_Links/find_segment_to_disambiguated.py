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
    query = {"generated_by": "link_disambiguator"}
    broken_link_res = broken_links(query=query, ref_or_query="query", auto_links=args.auto_links,
                                   manual_links=args.manual_links, delete_links=args.delete_links,
                                   check_text_exists=args.check_text_exists)
    with open("segment_to_disambiguated.csv", 'w') as f:
        writer = csv.writer(f)
        for l in broken_link_res:
            writer.writerow(eval(l.split("\t")[0]))