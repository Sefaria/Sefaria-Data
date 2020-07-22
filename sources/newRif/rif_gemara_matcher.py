import re
import os
import csv
import django
django.setup()
from functools import partial
from sefaria.model import *
from rif_utils import path, remove_metadata, tags_map, get_hebrew_masechet
from data_utilities.dibur_hamatchil_matcher import match_ref
from sefaria.system.exceptions import InputError

def base_tokenizer(string):
    return re.sub(r'<.*?>', '', string).split()

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
    for row in data:
        if tags_map[masechet]['gemara_refs'] in row['content']:
            if remove_metadata(row['content'].split(tags_map[masechet]['gemara_refs'])[0], masechet) != '':
                splitted_data[current_ref].append(row)
            for ref in re.findall(r'{}(.*?){}'.format(tags_map[masechet]['gemara_refs'], tags_map[masechet]['end_tag']), row['content']):
                if ref not in list(splitted_data):
                    splitted_data[ref] = []
                splitted_data[ref].append(row)
                current_ref = ref

    for page in splitted_data:
        try:
            gemara_text = Ref(heb_masechet+' '+page).text('he')
        except InputError:
            print(heb_masechet+' '+page+' didnt find')
        rif_text = [section['content'] for section in splitted_data[page]]
        report.append(match_ref(gemara_text, rif_text, base_tokenizer, dh_extract_method=partial(remove_metadata, masechet=masechet)))
        new_report = []
        for dict in report:
            for n in range(len(dict['matches'])):
                new_report.append({'matches':dict['matches'][n], 'match_word_indices':dict['match_word_indices'][n], 'gemara':dict['match_text'][n][0], 'rif':dict['match_text'][n][1]})
    with open(path+'/gemara_links/{}.csv'.format(masechet), 'w', newline='', encoding='utf-8') as fp:
        awriter = csv.DictWriter(fp, fieldnames=['matches', 'match_word_indices', 'gemara', 'rif'])
        awriter.writeheader()
        for item in new_report:
            awriter.writerow(item)
    break
