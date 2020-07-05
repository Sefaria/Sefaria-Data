import os
import csv
import re
from sefaria.model import *

path = os.path.dirname(os.path.abspath("top_level_file.txt"))

def removeinbetween(stringtoclean, sub1, sub2):
    return re.sub(sub1+'.*?'+sub2, '', stringtoclean)

def remove_notes(string, masechet):
    for note_tag in [tags_map[masechet][tag] for tag in ['gemara_refs', 'notes', 'tanakh_refs']]:
        removeinbetween(string, note_tag, map[masechet]['end_tag'])

def hebrewplus(string_to_clean, letters_to_remain=''):
    return re.sub(r"[^א-ת "+letters_to_remain+"]", '', string_to_clean)

def netlen(string): #length in words without oher text
    for tag in '346':
        string = removeinbetween(string, '@1'+tag, '@77')
    return len(hebrewplus(string).split())

def get_hebrew_masechet(masechet):
    return Ref(masechet).index.get_title('he')

def open_rif_file(masechet):
    for root, dirs, files in os.walk(os.getcwd()+'/rif'):
        for file in files:
            if get_hebrew_masechet(masechet) in file:
                return open(root+'/'+file, encoding = 'utf-8')

tags_map = {}
with open('map.csv', newline='', encoding = 'utf-8') as file:
    tags_map = {row['masechet']: row for row in csv.DictReader(file)}

for masechet in list(tags_map):
    tags_map[masechet]['note_reg'] = r'(?:{}|{}|{}).*?{}'.format(*[tags_map[masechet][tag] for tag in ['gemara_refs', 'notes', 'tanakh_refs', 'end_tag']])

rif_files = ([masechet, get_hebrew_masechet(masechet), open_rif_file(masechet)] for masechet in list(tags_map))
