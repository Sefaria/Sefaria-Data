import re
import csv
import copy
import json
import django
django.setup()
from functools import partial
from sefaria.model import *
from rif_utils import path, remove_metadata, tags_map, get_hebrew_masechet, hebrewplus, netlen2, unite_ref
from data_utilities.parallel_matcher import ParallelMatcher
from sefaria.system.exceptions import InputError
from scoremanager import ScoreManager

with open(f'{path}/talmud.json', encoding='utf-8') as fp:
    rt = json.load(fp)
def open_rashei_tevot(string):
    rt_dict = {}
    for key, value in rt.items():
        rt_dict[key[:-1]+'"'+key[-1]] = [subval for subval in value if value[subval]==max(value.values())][0]
    return ' '.join([rt_dict.get(i, i) for i in string.split()])

with open('words_remove.json') as fp:
    words = json.load(fp)
def remove_too_frequent(l):
    return [w for w in l]# if re.sub('^ו+', '', hebrewplus(w, '"')) not in words]

def base_tokenizer(string, masechet):
    string = remove_metadata(string, masechet)
    return remove_too_frequent(open_rashei_tevot(string).split())

def check_ref(string, masechet, gemara_text):
    string = re.sub(r'במכילתין|לקמן|לעיל|ע"ש|מכלתין|מכילתין|כאן|[\(\)\[\]]', '', string).strip()
    try:
        Ref(string)
        if string.strip() != 'דף': return string, 'just ref'
        else: return None
    except (InputError, AttributeError):
        try:
            Ref(masechet+' '+string)
            return masechet + ' ' + string, 'just ref'
        except InputError:
            if string == 'שם':
                return gemara_text if gemara_text else ('1', 11) #if gemara text is none, returning something
            elif string == 'שם ע"א' and gemara_text:
                return Ref(gemara_text[0]).tref.replace(':', '.'), gemara_text[1]
            elif string == 'שם ע"ב' and gemara_text:
                return Ref(gemara_text[0]).tref.replace('.', ':'), gemara_text[1]
            elif 'דף' in string:
                if string.startswith('דף'):
                    try:
                        Ref(f'{gemara_text[0].split()[0]} {string}')
                        return f'{gemara_text[0].split()[0]} {string}', 'just ref'
                    except InputError:
                        print(string, f'{gemara_text[0].split()[0]} {string}')
                if string.startswith('שם'):
                    try:
                        Ref(string.replace('שם', gemara_text[0].split()[0]))
                        return string.replace('שם', gemara_text[0].split()[0]), 'just ref'
                    except InputError:
                        print(string, string.replace('שם', gemara_text[0].split()[0]))
                print('daf but not ref', string)
            return None

def check_note_and_ref(string, masechet):
    try: #maybe first 3 words are ref and the other is note
        Ref(' '.join([masechet]+string.split()[:3]))
        return ' '.join([masechet] + string.split()[:3]), 'ref and note'
    except InputError:
        return None

def handle_tanakh_refs(string, masechet, prev):
    tanakh_ref = tags_map[masechet]['tanakh_refs']
    end_tag = tags_map[masechet]['end_tag']
    if tanakh_ref not in string:
        if end_tag in string:
            print('end tag in string', string)
        return string, prev
    ref = ''
    for ref in re.findall(f'{tanakh_ref}([^@]*){end_tag}', string):
        try:
            if 'Tanakh' not in Ref(ref).index.categories:
                print(masechet, 'ref not tanakh', ref)
        except:
            try:
                newref = ref.replace('מ"א', 'מלכים א').replace('מ"ב', 'מלכים ב')
                Ref(newref)
                string = string.replace(ref, newref)
                ref = newref
            except:
                if ref == 'שם':
                    string = string.replace(tanakh_ref+ref+end_tag, tanakh_ref+prev+end_tag, 1)
                    ref = prev
                else:
                    try:
                        if 'שמואל' not in prev and 'מלכים' not in prev:
                            book = prev.split()[0]
                        else:
                            book = ' '.join(prev.split()[:2])
                        newref = ref.replace('שם', book)
                        Ref(newref)
                        string = string.replace(tanakh_ref+ref+end_tag, tanakh_ref+newref+end_tag)
                        ref = newref
                    except InputError:
                        print(masechet, 'not a ref', ref)
        prev = ref
    string = re.sub(f'{tanakh_ref} *([^@]*) *{end_tag}', r'(\1)', string)
    if tanakh_ref in string or end_tag in string:
        print('still has tanakh or end tag', string)
    return string, ref

def execute():
    ref_and_note_tag = '%@%'
    for masechet in list(tags_map):
        print(masechet)
        heb_masechet = get_hebrew_masechet(masechet)
        data = []
        links = []
        new_data = []
        prev = ''
        current_ref = 'דף ב.'
        oldpage = None
        splitted_data = {current_ref: []}
        #score_manager = ScoreManager("words_dict.json")
        matcher = ParallelMatcher(partial(base_tokenizer, masechet=masechet), verbose=False)#, all_to_all=False)#, calculate_score=score_manager.get_score)
        ref_tag = tags_map[masechet]['gemara_refs']
        note_tag = tags_map[masechet]['notes']
        end_tag = tags_map[masechet]['end_tag']
        gemara_text = '1', 11

        with open(path+'/rif_csv/styled/'+masechet+'.csv', encoding='utf-8', newline='') as file:
            data = list(csv.DictReader(file))

        for row in data:
            page = row["page.section"].split(":")[0]
            if oldpage != page:
                par = 1
            else:
                par += 1
            oldpage = page
            row['page.section'] = f'{page}:{par}'
            row['content'] = re.sub(r'[\ufeff\n]', '', row['content'])
            if row['content'] == '':
                print('empty row in', row['page.section'])
                continue

            if note_tag in row['content']: #notes tag can be refs to another masechet. in that case, this replaceing the tag
                for note in re.findall(note_tag+'([^@<]*)'+end_tag, row['content']):
                    if check_ref(note, heb_masechet, gemara_text):
                        gemara_text = check_ref(note, heb_masechet, gemara_text) #a is not for use
                        row['content'] = row['content'].replace(note_tag+note, ref_tag+note)
                    elif check_note_and_ref(note, heb_masechet):
                        row['content'] = row['content'].replace(note_tag+note, ref_and_note_tag+note)
                        print('note and ref', masechet, note)

            newrow = copy.copy(row)
            row['content'] = re.sub(r'\(\*\)|\*\)|\*(?!.\))', '', row['content']) #removing (*) *) and any * that isn't from the form of (*.) which is a tag
            row['content'] = re.sub(ref_tag+' *([^@<]*) *'+end_tag, r' (\1) ', row['content'])
            row['content'] = re.sub(f'(?:{note_tag}|{ref_and_note_tag}) *([^@<]*) *{end_tag}', r'<sup>*</sup><i class="footnote">\1</i>', row['content'])
            row['content'] = re.sub(' (?:</i>|</i>) ', '</i>', row['content'])
            if any(tag in row['content'] for tag in [ref_tag, note_tag, ref_and_note_tag]):
                print('ref/note tag in', row['content'])
            row['content'], prev = handle_tanakh_refs(row['content'], masechet, prev)
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
                try:
                    current_ref, newrow['content'] = newrow['content'].split(end_tag, 1)
                except ValueError:
                    print('end tag in end', newrow['content'])
                if current_ref not in splitted_data: splitted_data[current_ref] = []
            splitted_data[current_ref].append(newrow)

        for ref in splitted_data:
            if check_ref(ref, heb_masechet, gemara_text):
                gemara_text = check_ref(ref, heb_masechet, gemara_text)
            elif check_note_and_ref(ref, heb_masechet):
                gemara_text = check_note_and_ref(ref, heb_masechet)
            else:
                print(heb_masechet, ref, 'didnt find')

            for section in splitted_data[ref]:
                if netlen2(section['content'], masechet) > 4:
                    tref_list = [gemara_text[0], (section['content'], 'rif')]
                    ver = 'Wikisource Talmud Bavli' if Ref(gemara_text[0]).is_bavli() else None
                    match_list = matcher.match(tref_list, return_obj=True, vtitle_list=[ver, None])
                    match_list = [item for item in match_list if 'rif' in [item.a.mesechta, item.b.mesechta] and [item.a.mesechta, item.b.mesechta] != ['rif', 'rif']]
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

if __name__ == '__main__':
    execute()
