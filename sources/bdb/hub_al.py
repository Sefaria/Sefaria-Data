import json
import re
import os
from bs4 import BeautifulSoup
import django
django.setup()
# from sefaria.model import *
import diff_match_patch as dmp_module

def get_al_ent(file_index, index):
    with open(f'alhatorah/{file_index}.json') as fp:
        al_ent = json.load(fp)
    try:
        key = sorted(al_ent['BDB'])[index]
        return {key: al_ent['BDB'][key]}
    except KeyError:
        print(i, 'no bdb. perhaps an aramaic v entry')

def get_al_text(al_ent):
    al_ent = list(al_ent.values())[0]
    al_ent = BeautifulSoup(al_ent, 'html.parser')
    return ' '.join(al_ent.text.split())

def is_hebrew(word):
    return all(1424 < ord(l) < 1525 for l in word)

def is_only_hebrew_letters(word):
    if type(word) != str:
        return
    return all(1487 < ord(l) < 1515 for l in word)

def first_hebrew_word(text):
    for word in text.split():
        word = re.sub('[\[\],\.]', '', word)
        if is_hebrew(word) or (re.search('^\[.*\]$', word) and is_hebrew(word[1:-1])):
            return word

if __name__ == '__main__':
    hub_nums = os.listdir('biblehub')
    hub_nums = [int(f.split('.')[0]) for f in hub_nums]
    al_files = os.listdir('alhatorah')
    al_dict = {}
    for fn in al_files:
        with open(f'alhatorah/{fn}') as fp:
            file = json.load(fp)
        if 'BDB' in file:
            for key in file["BDB"]:
                al_dict[f"{fn.replace('.json', '')}_{key}"] = {'hub': None}
    hub_dict = {}
    x=0

    for i in range(1, 8675):
        try:
            with open(f'biblehub/{i}.html') as fp:
                hub = BeautifulSoup(fp.read(), 'html.parser')
        except FileNotFoundError:
            continue

        hub_entries = []
        for p in hub.children:
            e = 0
            if p.font and 'class' in p.font.attrs and 'hebrew2' in p.font.attrs['class']:
                hub_entries.append(BeautifulSoup('', 'html.parser'))
                hub_dict[f'{i}_{e}'] = {'al': None}
            hub_entries[-1].append(p)

        for e, h_ent in enumerate(hub_entries):

            with open(f'bh_divided/{i}_{e}.html', 'w') as fp:
                fp.write(h_ent.prettify())

            h_ent = ' '.join(h_ent.text.split())
            h_ent = re.sub(r' ([\.\',\]])', r'\1', h_ent)
            h_ent = re.sub(r'(\[) ', r'\1', h_ent)

            if e == 0:
                al_ent = get_al_ent(i, e)
                if not al_ent:
                    hub_dict[f'{i}_{e}']['type'] = 'unknown'
                    continue
                al_text = get_al_text(al_ent)
                if al_text:
                    al_key = f'{i}_{list(al_ent)[0]}'
                    hub_dict[f'{i}_{e}']['al'] = al_key
                    hub_dict[f'{i}_{e}']['type'] = 'regular'
                    al_dict[al_key]['hub'] = f'{i}_{e}'
                else:
                    print('no text in al entry', al_key)
                    hub_dict[f'{i}_{e}']['al'] = al_key
                    hub_dict[f'{i}_{e}']['type'] = 'no text in al entry'
            else:
                first = first_hebrew_word(h_ent)
                if first:
                    first = re.sub('[\[\],\.ׁׂ]', '', first)
                if i == 8674:
                    hub_dict[f'{i}_{e}'] = {'type': 'ending entries'}
                elif len(h_ent.split()) < 20 and any(w in h_ent for w in ['see', 'q. v.']):
                    hub_dict[f'{i}_{e}'] = {'type': 'vide entry'}
                elif is_only_hebrew_letters(first) and len(first)==3:
                    hub_dict[f'{i}_{e}'] = {'type': 'root entry'}
                else:
                    try:
                        al_ent = get_al_ent(i, e)
                        al_key = f'{i}_{list(al_ent)[0]}'
                        hub_dict[f'{i}_{e}'] = {'type': 'regular',
                                                'al': al_key}
                        al_dict[al_key]['hub'] = f'{i}_{e}'
                    except (IndexError, TypeError):
                        al_ent = get_al_ent(i + 1, 0)
                        if i+1 not in hub_nums and al_ent:
                            al_key = f'{i+1}_{list(al_ent)[0]}'
                            if not al_dict[al_key]['hub']:
                                hub_dict[f'{i}_{e}'] = {'type': 'probably aramaic',
                                'al': al_key}
                                al_dict[al_key]['hub'] = f'{i}_{e}'
                            else:
                                hub_dict[f'{i}_{e}'] = {'type': 'unknown'}
                        else:
                            hub_dict[f'{i}_{e}'] = {'type': 'unknown'}

    with open('hub_dict.json', 'w') as fp:
        json.dump(hub_dict, fp)
    with open('al_dict.json', 'w') as fp:
        json.dump(al_dict, fp)
