import django

django.setup()
from tqdm import tqdm
import os
superuser_id = 171118
import csv
import re
from sefaria.model import *
from typing import List
from pprint import pprint
import copy
from bs4 import BeautifulSoup

def csv_to_list_of_lists(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        data = [row for row in reader]  # Convert each row into a list
    return data

def create_all_alt_titles_object():
    alt_titles = {}
    table = csv_to_list_of_lists("Mishne Torah Alt Titles.csv")
    for row in table[1:]:
        # alt_titles += [
        # {
        #     'en_title': row[0], 'he_title': row[1],
        #     'alt_titles': [title for title in row[2:] if title]
        # }]
        alt_titles[row[0]] = [title for title in row[2:] if title]
    return alt_titles

if __name__ == '__main__':
    alt_titles_dict = create_all_alt_titles_object()
    for index in library.get_indexes_in_category("Mishneh Torah", full_records=True):
        if not index.title.startswith("Mishneh Torah, "): continue
        last_term = list(list(index.nodes.get_match_templates())[0].get_terms())[-1]
        assert isinstance(last_term, NonUniqueTerm)
        for alt_title in alt_titles_dict[index.title]:
            # before adding a new title, ensure it doesn't already exist (this is left as an assignment to the reader)
            existing_titles = last_term.get_titles()
            if alt_title in existing_titles: continue
            last_term.add_title(alt_title, 'he')
            last_term.save()
