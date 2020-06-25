import os
import csv
import re
import django
django.setup()
from sefaria.model import *

path = os.path.dirname(os.path.abspath("top_level_file.txt"))

def cleanspaces(string):
    while any(space in string for space in ['  ', '( ', ' )', ' :', ' .']):
        for space in ['  ', '( ', ' )', ' :', ' .']:
            string = string.replace(space, space.replace(' ', '', 1))
    return string.strip()

def removeinbetween(stringtoclean, sub1, sub2):
    return re.sub(sub1+'.*?'+sub2, '', stringtoclean)

def remove_notes(string, masechet):
    for note_tag in [tags_map[masechet][tag] for tag in ['gemara_refs', 'notes', 'tanakh_refs']]:
        string = removeinbetween(string, note_tag, tags_map[masechet]['end_tag'])
    return string

def hebrewplus(string_to_clean, letters_to_remain=''):
    return re.sub(r"[^א-ת "+letters_to_remain+"]", '', string_to_clean)

def remove_metadata(string, masechet):
    string = remove_notes(string, masechet)
    string = re.sub(r'@00פרק .*? ', ' ', string)
    for mark in mefarshim_tags(masechet):
        string = re.sub(mark, '', string)
    string = hebrewplus(string, '"\'')
    return cleanspaces(string)

def netlen(string): #length in words without oher text
    for tag in '346':
        string = removeinbetween(string, '@1'+tag, '@77')
    return len(hebrewplus(string).split())

def get_hebrew_masechet(masechet):
    return Ref(masechet).index.get_title('he')

def open_rif_file(masechet, path='/rif'):
    for root, dirs, files in os.walk(os.getcwd()+path):
        for file in files:
            if get_hebrew_masechet(masechet) in file or masechet in file:
                return open(root+'/'+file, encoding = 'utf-8')

def mefarshim_tags(masechet):
    return [tags_map[masechet][tag] for tag in ['Shiltei HaGiborim', 'Bach on Rif', 'Chidushei An"Sh', 'Hagaot Chavot Yair', 'Hagaot meAlfas Yashan', 'Ein Mishpat Rif']]

tags_map = {}
with open('map.csv', newline='', encoding = 'utf-8') as file:
    tags_map = {row['masechet']: row for row in csv.DictReader(file)}

for masechet in list(tags_map):
    tags_map[masechet]['note_reg'] = r'(?:{}|{}|{}).*?{}'.format(*[tags_map[masechet][tag] for tag in ['gemara_refs', 'notes', 'tanakh_refs', 'end_tag']])

rif_files = ([masechet, get_hebrew_masechet(masechet), open_rif_file(masechet)] for masechet in list(tags_map))
segmented_rif_files = ([masechet, get_hebrew_masechet(masechet), open_rif_file(masechet, '/rif_segmented')] for masechet in list(tags_map))
