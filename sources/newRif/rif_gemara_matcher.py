import re
import os
import csv
import copy
import django
django.setup()
from functools import partial
from sefaria.model import *
from rif_utils import path, remove_metadata, tags_map, get_hebrew_masechet, hebrewplus, netlen2
from linking_utilities.dibur_hamatchil_matcher import match_ref
from sefaria.system.exceptions import InputError

def base_tokenizer(string):
    return hebrewplus(string, '"\'').split()

def rif_dh(string, masechet):
    return ' '.join(remove_metadata(string, masechet).split()[:7])

for masechet in list(tags_map):
    heb_masechet = get_hebrew_masechet(masechet)
    data = []
    report = []
    for root, dirs, files in os.walk(os.getcwd()+'/rif_csv'):
        for file in files:
            if masechet in file:
                with open(path+'/rif_csv/'+file, encoding='utf-8', newline='') as file:
                    data = list(csv.DictReader(file))

    splitted_data = {}
    ref_tag = tags_map[masechet]['gemara_refs']
    for row in data:
        while ref_tag in row['content']:
            if row['content'].index(ref_tag) != 0:
                newrow = copy.copy(row)
                newrow['content'], row['content'] = newrow['content'].split(ref_tag, 1)
                if remove_metadata(newrow['content'], masechet) != '':
                    splitted_data[current_ref].append(newrow)
            else:
                row['content'] = row['content'][3:]
            current_ref, row['content'] = row['content'].split(tags_map[masechet]['end_tag'], 1)
            if current_ref not in splitted_data: splitted_data[current_ref] = []
        splitted_data[current_ref].append(row)

    for page in splitted_data:
        try:
            gemara_text = Ref(heb_masechet+' '+page).text('he')
        except InputError:
            print(heb_masechet+' '+page+' didnt find')
        rif_text = [section['content'] for section in splitted_data[page] if netlen2(section['content'], masechet)>3]
        report.append(match_ref(gemara_text, rif_text, base_tokenizer, dh_extract_method=partial(rif_dh, masechet=masechet), word_threshold=0.35))
        new_report = []
        for dict in report:
            for n in range(len(dict['matches'])):
                new_report.append({'matches':dict['matches'][n], 'match_word_indices':dict['match_word_indices'][n], 'gemara':dict['match_text'][n][0], 'rif':dict['match_text'][n][1]})
    f = 0
    for dict in new_report:
        if dict['matches'] == None: f+=1
    print('{}% failed'.format(100*f/len(new_report)))

    with open(path+'/gemara_links/{}.csv'.format(masechet), 'w', newline='', encoding='utf-8') as fp:
        awriter = csv.DictWriter(fp, fieldnames=['matches', 'match_word_indices', 'gemara', 'rif'])
        awriter.writeheader()
        for item in new_report:
            awriter.writerow(item)
    break
