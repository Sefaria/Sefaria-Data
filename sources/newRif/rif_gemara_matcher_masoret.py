import re
import csv
import copy
import json
import django
django.setup()
from functools import partial
from sefaria.model import *
from rif_utils import path, remove_metadata, tags_map, get_hebrew_masechet, hebrewplus, netlen2, unite_ref
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from sefaria.system.exceptions import InputError

def base_tokenizer(string, masechet):
    return remove_metadata(string, masechet).split()

def check_ref(string, masechet):
    string = re.sub('במכילתין|לקמן|לעיל|ע"ש|מכלתין|מכילתין|כאן|[\(\)\[\]]', '', string)
    try:
        Ref(string)
        if string.strip() != 'דף': return string, 'just ref'
        else: return None
    except (InputError, AttributeError):
        try:
            Ref(masechet+' '+string)
            return masechet + ' ' + string, 'just ref'
        except InputError:
            return None

def check_note_and_ref(string, masechet):
    try: #maybe first 2 words are ref and the other is note
        Ref(' '.join([masechet]+string.split()[:2]))
        return ' '.join([masechet] + string.split()[:2]), 'ref and note'
    except InputError:
        return None

if __name__ == "__main__":
    ref_and_note_tag = '%@%'
    for masechet in list(tags_map):
        heb_masechet = get_hebrew_masechet(masechet)
        data = []
        links = []
        new_data = []
        current_ref = 'דף ב.'
        splitted_data = {current_ref: []}
        matcher = ParallelMatcher(partial(base_tokenizer, masechet=masechet), verbose=False)
        ref_tag = tags_map[masechet]['gemara_refs']
        note_tag = tags_map[masechet]['notes']
        end_tag = tags_map[masechet]['end_tag']

        with open(path+'/rif_csv/rif_'+masechet+'.csv', encoding='utf-8', newline='') as file:
            data = list(csv.DictReader(file))

        for row in data:
            row['content'] = re.sub(r'[\ufeff\n]', '', row['content'])
            if row['content'] == '':
                print('empty row in', row['page.section'])
                continue

            if note_tag in row['content']: #notes tag can be refs to another masechet. in that case, this replaceing the tag
                for note in re.findall(note_tag+'([^@<]*)'+end_tag, row['content']):
                    if check_ref(note, heb_masechet):
                        row['content'] = row['content'].replace(note_tag+note, ref_tag+note)
                    elif check_note_and_ref(note, heb_masechet):
                        row['content'] = row['content'].replace(note_tag+note, ref_and_note_tag+note)
                        print('note and ref', masechet, note)

            newrow = copy.copy(row)
            row['content'] = re.sub(ref_tag+'([^@<]*)'+end_tag, r' (\1) ', row['content'])
            row['content'] = re.sub(note_tag+'|'+ref_and_note_tag+'([^@<]*)'+end_tag, r'<sup>*</sup><i class="footnote">\1</i>', row['content'])
            row['content'] = row['content'].replace(' </i>', '</i> ')
            new_data.append(row)

            with_ref_tag = ref_tag + '|' + ref_and_note_tag
            while re.search(with_ref_tag, newrow['content']):
                if re.search(with_ref_tag, newrow['content']).start() != 0:
                    newrow0 = copy.copy(newrow)
                    newrow0['content'], newrow['content'] = re.split(with_ref_tag, newrow['content'], 1)
                    if remove_metadata(newrow0['content'], masechet) != '':
                        splitted_data[current_ref].append(newrow0)
                else:
                    newrow['content'] = re.sub(with_ref_tag, '', newrow['content'], 1)
                current_ref, newrow['content'] = newrow['content'].split(end_tag, 1)
                if current_ref not in splitted_data: splitted_data[current_ref] = []
            splitted_data[current_ref].append(newrow)

        for ref in splitted_data:
            if check_ref(ref, heb_masechet):
                gemara_text = check_ref(ref, heb_masechet)
            elif check_note_and_ref(ref, heb_masechet):
                gemara_text = check_note_and_ref(ref, heb_masechet)
            else:
                print(heb_masechet, ref, 'didnt find')

            for section in splitted_data[ref]:
                if netlen2(section['content'], masechet) > 4:
                    tref_list = [gemara_text, (section['content'], 'rif')]
                    match_list = matcher.match(tref_list, return_obj=True)
                    match_list = [item.a.ref if item.a.mesechta!='rif' else item.b.ref for item in match_list]
                    match_list = unite_ref(match_list)
                    for item in match_list:
                        links.append([{
                        "refs": ["Rif {} {}".format(masechet, section['page.section']), item],
                        "type": "Commentary",
                        "auto": True,
                        "generated_by": 'rif gemara matcher'
                        }])

        with open(path+'/gemara_links/{}.json'.format(masechet), 'w') as fp:
            json.dump(links, fp)

        with open(path+'/rif_gemara_refs/rif_{}.csv'.format(masechet), 'w', encoding='utf-8', newline = '') as file:
            awriter = csv.DictWriter(file, fieldnames=['page.section', 'content'])
            awriter.writeheader()
            for item in new_data: awriter.writerow(item)
