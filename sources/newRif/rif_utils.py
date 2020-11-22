import os
import csv
import re
import django
django.setup()
from sefaria.model import *

path = os.path.dirname(os.path.abspath("top_level_file.txt"))

def cleanspaces(string):
    string = re.sub (' +', ' ', string)
    string = re.sub(r' ([\)\]:\.])|([\(\[]) ', r'\1\2', string)
    return string.strip()

def removeinbetween(stringtoclean, sub1, sub2):
    return re.sub(sub1+'.*?'+sub2, '', stringtoclean)

def remove_notes(string, masechet):
    for note_tag in [tags_map[masechet][tag] for tag in ['gemara_refs', 'notes', 'tanakh_refs']]:
        string = removeinbetween(string, note_tag, tags_map[masechet]['end_tag'])
    return string

def hebrewplus(string_to_clean, letters_to_remain=''): #note addimg \ for letters which need that
    return re.sub(r"[^א-ת "+letters_to_remain+"]", '', string_to_clean)

def remove_metadata(string, masechet):
    string = remove_notes(string, masechet)
    string = re.sub(r'@00פרק .*? ', ' ', string)
    string = re.sub(mefarshim_tags(masechet), '', string)
    string = hebrewplus(string, '"\'')
    return cleanspaces(string)

def remove_meta_and_html(string, masechet):
    string = re.sub('<sup>.*?</i>', '', string)
    return remove_metadata(string, masechet)

def netlen(string): #length in words without oher text
    for tag in '346':
        string = removeinbetween(string, '@1'+tag, '@77')
    return len(hebrewplus(string).split())

def netlen2(string, masechet): #a better version.
    string = re.sub(' . ', '', remove_metadata(string, masechet))
    return len(string.split())

def get_hebrew_masechet(masechet):
    return Ref(masechet).index.get_title('he')

def open_rif_file(masechet, path='/rif'):
    with open(os.getcwd()+path+'/rif_'+masechet+'.txt', encoding = 'utf-8') as fp:
        data = fp.read()
    return data

def mefarshim_tags(masechet):
    return r'{}|{}|{}|{}|{}|{}'.format(*[tags_map[masechet][tag] for tag in ['Shiltei HaGiborim', 'Bach on Rif', 'Chidushei An"Sh', 'Hagaot Chavot Yair', 'Hagaot meAlfas Yashan', 'Ein Mishpat Rif']])

def unite_ref(refs: list) -> list:
    '''
    :param list refs: list of Refs and trefs, all to the same page of gemara, to one line or range of lines
    :return: list of trefs withno overlapping, refering to range of lines when possible
    '''

    if refs == []: return []
    refs = [ref.tref if type(ref)==Ref else ref for ref in refs]
    print(refs)
    base_ref = refs[0].split(':')[0]
    lines = set()
    for ref in refs:
        if ':' not in ref:
            return [ref]
        ref_lines = ref.split(':')[1]
        if '-' in ref_lines:
            start, end = [int(a) for a in ref_lines.split('-')]
            end += 1
            lines = lines | set(range(start, end))
        else:
            lines.add(int(ref_lines))

    start = 0
    new_ref_lines = []
    for line in sorted(lines):
        if start == 0: start = line
        if line+1 in lines: continue
        else:
            if line == start:
                new_ref_lines.append('{}:{}'.format(base_ref, start))
            else:
                new_ref_lines.append('{}:{}-{}'.format(base_ref, start, line))
            start = 0

    return new_ref_lines

def unite_ref_pages(refs):
    if refs == []: return []
    refs = [ref.tref if type(ref)==Ref else ref for ref in refs]
    refs_dict = {ref.split()[-1].split(':')[0]: [] for ref in refs}
    for ref in refs:
        refs_dict[ref.split()[-1].split(':')[0]].append(ref)
    for key in refs_dict:
        refs_dict[key] = unite_ref(refs_dict[key])
    return [item for x in list(refs_dict.values()) for item in x]

def main_mefaresh(masechet):
    for mefaresh in ['Ran', 'Nimmukei Yosef', 'Rabbenu Yonah', 'Rabbenu Yehonatan of Lunel']:
        if tags_map[masechet][mefaresh] == 'Digitized' or tags_map[masechet][mefaresh] == 'shut':
            return mefaresh

tags_map = {}
with open('map.csv', newline='', encoding = 'utf-8') as file:
    tags_map = {row['masechet']: row for row in csv.DictReader(file)}

commentaries = {}
with open('commentaries.csv', newline='', encoding = 'utf-8') as file:
    commentaries = {row['num']: row for row in csv.DictReader(file)}

maor_tags = {}
with open('maor_tags.csv', newline='', encoding = 'utf-8') as file:
    maor_tags = {row['masechet']: row for row in csv.DictReader(file)}

for masechet in list(tags_map):
    tags_map[masechet]['note_reg'] = r'(?:{}|{}|{}).*?{}'.format(*[tags_map[masechet][tag] for tag in ['gemara_refs', 'notes', 'tanakh_refs', 'end_tag']])

rif_files = ([masechet, get_hebrew_masechet(masechet), open_rif_file(masechet)] for masechet in list(tags_map))
segmented_rif_files = ([masechet, get_hebrew_masechet(masechet), open_rif_file(masechet, '/rif_segmented')] for masechet in tags_map)

def maor_godel(masechet):
    if masechet in library.get_indexes_in_category(["Talmud", "Bavli", "Seder Nashim"])+library.get_indexes_in_category(["Talmud", "Bavli", "Seder Nezikin"]):
        return 'HaGadol', 'הגדול'
    else:
        return 'HaKatan', 'הקטן'
