import django
django.setup()
from sefaria.model import *
import re
import csv
from noam2 import match
from gra import find_ref, match_between_refs

def get_essence_of_dh(dh):
    return re.split('ומשני|ומפרש|ומקשי|ו?ה"ג', dh, 1)[-1]

def get_dh(text):
    if '@11' in text:
        for occ in re.findall('@11(.*?@33)', text):
            yield get_essence_of_dh(occ)
    else:
        yield ' '.join(text.split()[:7])

with open('gra2.csv') as fp:
    r = csv.DictReader(fp)
    fieldnames = r.fieldnames
    rows = list(r)
for row in rows:
    if not row['base text ref']:
        mas = row['masechet']
        perek = row['perek'] or None
        halakha = row['halakha'] or None
        page = row['page'] or None
        gen_ref = find_ref(mas, perek, halakha, page)
        try:
            Ref(gen_ref)
        except:
            print(f'no ref: {gen_ref}. vars: {mas}, {page}, {halakha}, {page}')
            continue
        if not gen_ref:
            continue
        for dh in get_dh(row['comment']):
            ma = match(gen_ref, dh)
            if ma:
                row['base text ref'] = ma
                row['iteration2'] = 'X'
                break
rows = match_between_refs(rows)
with open('gra.csv', 'w', encoding='utf-8', newline='') as fp:
    writer = csv.DictWriter(fp, fieldnames=['file', 'masechet', 'commentary', 'perek', 'halakha', 'page', 'comment', 'dh',
                                            'base text ref', 'match by context', 'base text', 'iteration2'])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)


