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
#
# total_ls = [(l.refs[0], l.refs[1]) for l in LinkSet()]
#segment_ls finds any link with a segment in either ref so the "difference" leaves us with only those links
#where BOTH sides are section refs
# segment_ls = [(l.refs[0], l.refs[1]) for l in LinkSet({"refs": {"$regex": ":"}})]
# section_ls = set(total_ls).difference(set(segment_ls))

# section_ls = LinkSet({"refs": {"$regex": "\s[\dab]{1,4}$"}})
# with open("section links.csv", 'w') as f:
#     writer = csv.writer(f)
#     for link in section_ls:
#         writer.writerow(link.refs)
#
# print(len(section_ls))
# print("GOT THERE")
links = []
with open("section links.csv", 'r') as f:
    for row in csv.reader(f):
        links.append(row)

""" The main function, runs when called from the CLI"""
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
    pesachim_counter = Counter()
    finds = []
    for n, link in enumerate(links):
        for i, ref in enumerate(link):
            try:
                section_level = Ref(ref).is_section_level()
            except InputError as e:
                pass
            if section_level:
                other_ref = link[1-i]
                other_ref_is_empty = False
                try:
                    other_ref_is_empty = Ref(other_ref).is_empty()
                except InputError as e:
                    other_ref_is_empty = True
                if other_ref_is_empty:
                    if ref.startswith("Pesachim"):
                        pesachim_counter[Ref(other_ref).index.title] += 1
                    finds.append([ref, other_ref])
                    # finds += broken_links(tref=ref, ref_or_query="ref", auto_links=args.auto_links,
                    #                            manual_links=args.manual_links, delete_links=args.delete_links,
                    #                            check_text_exists=args.check_text_exists)
                break



    print(pesachim_counter)
# check pesachim section level issues and see if they are here as well

    print("\nSegmented")
    for tuple in count_per_book_A.most_common(15):
        print(tuple)
    print("\nUnsegmented")
    for tuple in count_per_book_B.most_common(15):
        print(tuple)


# Section to no text should be deleted

# {"refs": /Genesis \d{1,2}$/}
# Segment to no text AND link_disambiguator was used, consider stepping back to section level and redoing disambiguation
# if that gets us to the same place, just delete it
