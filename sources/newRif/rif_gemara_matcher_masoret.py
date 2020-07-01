import re
import csv
import copy
import django
django.setup()
from functools import partial
from sefaria.model import *
from rif_utils import path, remove_metadata, tags_map, get_hebrew_masechet, hebrewplus, netlen2, unite_ref
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from sefaria.system.exceptions import InputError

def base_tokenizer(string, masechet):
    return remove_metadata(string, masechet).split()

for masechet in list(tags_map):
    heb_masechet = get_hebrew_masechet(masechet)
    data = []
    report = []
    current_ref = 'דף ב.'
    splitted_data = {current_ref: []}
    matcher = ParallelMatcher(partial(base_tokenizer, masechet=masechet), verbose=False)

    with open(path+'/rif_csv/rif_'+masechet+'.csv', encoding='utf-8', newline='') as file:
        data = list(csv.DictReader(file))

    ref_tag = tags_map[masechet]['gemara_refs']
    for row in data:
        row['content'] = row['content'].replace('\ufeff', '')
        if row['content'] == '': continue
        while ref_tag in row['content']:
            if row['content'].index(ref_tag) != 0:
                newrow = copy.copy(row)
                newrow['content'], row['content'] = newrow['content'].split(ref_tag, 1)
                if remove_metadata(newrow['content'], masechet) != '':
                    splitted_data[current_ref].append(newrow)
            else:
                row['content'] = row['content'][3:]
            print(row['content'])
            current_ref, row['content'] = row['content'].split(tags_map[masechet]['end_tag'], 1)
            if current_ref not in splitted_data: splitted_data[current_ref] = []
        print(masechet, row['content'])
        splitted_data[current_ref].append(row)

    for page in splitted_data:
        try:
            Ref(heb_masechet+' '+page).text('he')
            gemara_text = heb_masechet + ' ' + page
        except InputError:
            print(heb_masechet+' '+page+' didnt find')
        for section in splitted_data[page]:
            if netlen2(section['content'], masechet) > 4:
                tref_list = [gemara_text, (section['content'], 'rif')]
                match_list = matcher.match(tref_list, return_obj=True)
                if match_list == []:
                    report.append({'ref': '', 'gemara': '', 'rif': section['content']})
                else:
                    match_list = [item.a.ref for item in match_list]
                    match_list = unite_ref(match_list)
                    for ref in match_list:
                        report.append({'ref': ref, 'gemara': Ref(ref).text('he').text, 'rif': section['content']})

    with open(path+'/gemara_links/{}-masoret.csv'.format(masechet), 'w', newline='', encoding='utf-8') as fp:
        awriter = csv.DictWriter(fp, fieldnames=['ref', 'gemara', 'rif'])
        awriter.writeheader()
        for item in report:
            awriter.writerow(item)
