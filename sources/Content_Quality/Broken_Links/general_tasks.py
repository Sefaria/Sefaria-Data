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
from sources.Content_Quality.Broken_Links.redisambiguate import redisambiguate

def run_section_links(delete=False):
    links = []
    finds = []
    with open("section links.csv", 'r') as f:
        for row in csv.reader(f):
            links.append(row)
    for n, link in enumerate(links):
        for i, ref in enumerate(link):
            try:
                section_level = Ref(ref).is_section_level()
            except InputError as e:
                pass
            if section_level:
                other_ref = link[1 - i]
                other_ref_is_empty = False
                try:
                    other_ref_is_empty = Ref(other_ref).is_empty()
                except InputError as e:
                    other_ref_is_empty = True
                if other_ref_is_empty:
                    finds.append([ref, other_ref])
                    if delete:
                        link.delete()
    return finds

def run_broken_links():
    print("add_links_from_text")
    broken_links(query={"generated_by": "add_links_from_text"}, ref_or_query="query",
                                   auto_links=True,
                                   manual_links=True, delete_links=True,
                                   check_text_exists=True)
    print("commentary_links")
    broken_links(query={"generated_by": "add_commentary_links"}, ref_or_query="query",
                             auto_links=True,
                             manual_links=True, delete_links=True,
                             check_text_exists=True)

def run_disambiguator():
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

if __name__ == "__main__":
    print("disambiguating")
    run_disambiguator()
    print("deleting bad section links")
    run_section_links()
    print('deleting bad auto links')
    run_broken_links()