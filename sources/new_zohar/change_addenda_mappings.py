import json
import csv
import re
import django
django.setup()
from sefaria.model import *
from sefaria.utils.hebrew import gematria

with open('map_old_to_new-old2.json') as fp:
    mapping = json.load(fp)
with open('addenda_pages.csv') as fp:
    data = list(csv.DictReader(fp))
old_to_new = {}
for row in data:
    if row['siman']:
        siman = gematria(row['siman']) - 160
    seg = row['ref'].split(':')[1]
    base = ' '.join(row['ref'].split()[:-1]).replace('Zohar', 'Zohar TNNNG')
    old_to_new[row['ref'].replace('Zohar', 'Zohar TNNNG')] = f'{base} {siman}:{seg}'
for k in mapping:
    if mapping[k]:
        if mapping[k] in old_to_new:
            mapping[k] = old_to_new[mapping[k]]
        elif 'Addenda' in mapping[k]:
            old_val = mapping[k].replace('Zohar TNNNG', 'Zohar')
            if '-' in old_val:
                first = old_val.split('-')[0]
                last = re.sub('\d*\-', '', old_val)
            else:
                first = last = old_val
            found = False
            for row in data:
                if f'{first}:' in row['ref']:
                    news = row['ref']
                    break
            for row in data:
                if f'{last}:' in row['ref']:
                    newl = row['ref']
            news, newl = news.replace('Zohar', 'Zohar TNNNG'), newl.replace('Zohar', 'Zohar TNNNG')
            new = Ref(f'{old_to_new[news].replace("For ", "")}-{old_to_new[newl].replace("For ", "")}').normal()
            mapping[k] = new
        mapping[k] = mapping[k].replace('For ', '')
with open('map_old_to_new.json', 'w') as fp:
    json.dump(mapping, fp)

