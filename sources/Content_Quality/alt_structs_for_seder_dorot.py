# -*- coding: utf-8 -*-
import urllib
import json
import pdb
import os
import sys
from bs4 import BeautifulSoup
import re
from sources.functions import *
with open("Seder HaDorot - he - Seder HaDorot - Seder HaDorot - he - Seder HaDorot.csv", 'r') as f:
    rows = list(csv.reader(f))
text = defaultdict(dict)
curr_letter = ''
for i, row in enumerate(rows[5:]):
    ref, alt, letter = row[0], row[2], row[3]
    alt = alt.strip()
    letter = letter.strip()
    node = " ".join(ref.split(",")[1].split()[:-1])
    if node not in text:
        text[node] = {}
        curr_letter = ''
    if len(letter) == 1 and letter != curr_letter:
        assert abs(ALPHABET_22.index(letter) - ALPHABET_22.index(curr_letter)) == 1 or curr_letter == ""
        curr_letter = letter
        text[node][curr_letter] = []
    if len(alt) > 0:
        try:
            assert curr_letter in [x[0] for x in alt.split()]
        except AssertionError as e:
            print(curr_letter)
            print(row[2])
            print(node)
            print()
        try:
            text[node][curr_letter].append((alt, ref, len(text[node][curr_letter])+1))
        except Exception as e:
            print("Skipping...")

#index = get_index_api("Seder HaDorot", server="https://new-shmuel.cauldron.sefaria.org")
index = {'title': 'Seder HaDorot', 'categories': ['Reference', 'Encyclopedic Works'], 'schema': {'nodes': [{'nodeType': 'JaggedArrayNode', 'depth': 1, 'addressTypes': ['Integer'], 'sectionNames': ['Paragraph'], 'sharedTitle': 'Introduction', 'key': 'Introduction'}, {'nodes': [{'nodeType': 'JaggedArrayNode', 'depth': 2, 'addressTypes': ['Integer', 'Integer'], 'sectionNames': ['Chapter', 'Paragraph'], 'default': True, 'key': 'default'}, {'nodeType': 'JaggedArrayNode', 'depth': 2, 'addressTypes': ['Integer', 'Integer'], 'sectionNames': ['Chapter', 'Paragraph'], 'titles': [{'text': 'Index', 'lang': 'en', 'primary': True}, {'text': 'מפתח לסדר הדורות', 'lang': 'he', 'primary': True}], 'key': 'Index'}], 'titles': [{'text': 'Almanac', 'lang': 'en', 'primary': True}, {'text': 'סדר ימות עולם', 'lang': 'he', 'primary': True}], 'key': 'Almanac'}, {'nodeType': 'JaggedArrayNode', 'depth': 2, 'addressTypes': ['Integer', 'Integer'], 'sectionNames': ['Chapter', 'Paragraph'], 'titles': [{'text': 'Tanaim and Amoraim', 'lang': 'en', 'primary': True}, {'text': 'סדר תנאים ואמוראים', 'lang': 'he', 'primary': True}], 'key': 'Tanaim and Amoraim'}, {'nodeType': 'JaggedArrayNode', 'depth': 2, 'addressTypes': ['Integer', 'Integer'], 'sectionNames': ['Chapter', 'Paragraph'], 'sharedTitle': 'Authors', 'key': 'Authors'}, {'nodeType': 'JaggedArrayNode', 'depth': 2, 'addressTypes': ['Integer', 'Integer'], 'sectionNames': ['Chapter', 'Paragraph'], 'titles': [{'text': 'Compositions', 'lang': 'en', 'primary': True}, {'text': 'סדר ספרים', 'lang': 'he', 'primary': True}], 'key': 'Compositions'}, {'nodeType': 'JaggedArrayNode', 'depth': 1, 'addressTypes': ['Integer'], 'sectionNames': ['Paragraph'], 'sharedTitle': 'Haggahot', 'key': 'Haggahot'}], 'titles': [{'text': 'סדר הדורות', 'lang': 'he', 'primary': True}, {'text': 'Seder HaDorot', 'lang': 'en', 'primary': True}], 'key': 'Seder HaDorot'}}
text.pop("")
text.pop("Almanac")
text.pop("Introduction")
text.pop("Haggahot")
titles = {}
titles['Tanaim and Amoraim'] = 'סדר תנאים ואמוראים'
titles['Compositions'] = 'סדר ספרים'
index['alt_structs'] = {}
for nodestr in text:
    index['alt_structs'][nodestr] = {'nodes': []}
    # outermost_node = SchemaNode()
    # outermost_node.key = nodestr
    # if nodestr == 'Authors':
    #     outermost_node.add_shared_term(nodestr)
    # else:
    #     outermost_node.add_primary_titles(nodestr, titles[nodestr])
    for letter in text[nodestr]:
        letter_node = SchemaNode()
        letter_node.add_primary_titles(f'{ALPHABET_22.index(letter)+1}', letter)
        letter_node.key = f'{ALPHABET_22.index(letter)+1}'
        for alt, ref, i in text[nodestr][letter]:
            node = ArrayMapNode()
            try:
                #en = Term().load({"titles.he": alt}).name
                node.add_primary_titles(f"{i}", alt)
                node.depth = 0
                node.wholeRef = ref
                node.refs = []
                node.validate()
                letter_node.append(node)
            except:
                print(alt)
        letter_node.validate()
        index['alt_structs'][nodestr]['nodes'].append(letter_node.serialize())

Index(index).save()