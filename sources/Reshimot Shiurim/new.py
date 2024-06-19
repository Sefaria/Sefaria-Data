import csv
import re
import django
django.setup()
from sefaria.model import *
from sefaria.utils.hebrew import gematria
from sefaria.utils.talmud import section_to_daf
from linking_utilities.dibur_hamatchil_matcher import match_ref, match_text

Y,N=0,0

def parse_default(rows):
    text = []
    for row in rows:
        if row['page']:
            daf = gematria(row['page']) - 84
            amud = 2 if row['page'].endswith(':') else 1
            page = daf * 2 + amud - 2
            if len(text) > page:
                print('going reverse')
            text += [[] for _ in range(page-len(text))]
        text.append(row['text'])

def extract_dh(string):
    string = re.sub("^משנה|מתני'|גמ'|גמ\.|גמרא", '', string)
    string = re.sub('\.', '', string).strip()
    string = re.split("ו?כו'|\.", string)[0]
    string = ' '.join(string.split()[:7])
    return string

def match_gmara(ref, text):
    base_text = ref.text('he', 'Wikisource Talmud Bavli')
    match = match_ref(base_text, [text], lambda x: x.split(), dh_extract_method=extract_dh)['matches'][0]
    return match

def mtach_dh_to_dhs(dh, dhs):
    new = []
    for i, line in enumerate(dhs, 1):
        for j, segment in enumerate(line, 1):
            new.append({'indexes': (i, j), 'text': segment})
    matches = match_text(dh.split(), [x['text'] for x in new])
    for match, element in zip(matches['matches'], new):
        element['score'] = match[0] - match[1]
    new.sort(key=lambda x: x['score'])
    matched = new[0]
    if matched['score']:
        return matched['indexes']

def find_dh(ref, text):
    comments = Ref(ref).text('he').text
    comm_dh = text.split('ד"ה')[1].split('.')[0].split('וז"ל')[0].strip()
    dhs = []
    for i, talmud_line in enumerate(comments, 1):
        dhs.append([])
        for j, comment in enumerate(talmud_line, 1):
            dh = re.split('\.|\-', comment)[0].strip()
            dhs[-1].append(dh)
            if comm_dh in dh:
                return Ref(f'{ref}:{i}:{j}')
    indexes = mtach_dh_to_dhs(comm_dh, dhs)
    if indexes:
        return Ref(f'{ref} {indexes[0]}:{indexes[1]}')

def link(row, masechet):
    global Y,N
    daf = gematria(row['page'].split('-')[0]) - 84
    amud = 2 if row['page'].endswith(':') else 1
    page = daf * 2 + amud - 2
    ref = Ref(f'{masechet} {section_to_daf(page)}')
    text = row['text']
    text = text.split('</b>')[0]
    text = re.sub('<[^>]*>', '', text)
    # if re.search("^משנה|מתני'|גמ'|גמ\.|גמרא", text):
    #     pass
    if re.search('^רש"י', text):
        match = find_dh(f'Rashi on {ref}', text)
    elif re.search("^תוס'|תוספות", text):
        match = find_dh(f'Tosafot on {ref}', text)
    elif re.search("^בענין|בדין", text):
        return
    else: #gmara
        match = match_gmara(ref, text)
    if match:
        row['base ref'] = match
        row['base text'] = match.text('he').text
    if re.search('^רש"י', text) or re.search("^תוס'|תוספות", text):
        if match:
            Y+=1
        else:
            N+=1

title = 'Reshimot Shiurim'
for masechet in ['Sanhedrin', 'Horayot']:
    print(masechet)
    with open(f'{title} {masechet}.csv') as fp:
        data = list(csv.DictReader(fp))
    for row in data:
        if row['page']:
            link(row, masechet)
    with open(f'{title} {masechet}.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=["part", "page", "text", 'base ref', 'base text'])
        w.writeheader()
        for row in data:
            w.writerow(row)
print(Y,N)
