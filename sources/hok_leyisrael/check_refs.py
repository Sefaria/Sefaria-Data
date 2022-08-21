import os
import json
import re
import django
import requests
import csv
django.setup()
from sefaria.model import *

problems = []
with open('ids.json') as fp:
    ids = json.load(fp)

# for file in os.listdir('jsons'):
#     print(file)
#     with open(f'jsons/{file}') as fp:
#         sheet = json.load(fp)

for id in ids:
    url = f'https://hok.cauldron.sefaria.org/sheets/{id}'
    r = requests.get(f'https://hok.cauldron.sefaria.org/api/sheets/{id}')
    if r.status_code != 200:
        print(id, 'problem')
        continue
    sheet = r.json()
    p = []
    day = '6' if 'שישי' in sheet['title'] else 0
    # day = file.split('.')[0].split('-')[-1]
    if day == '6':
        if len([s for s in sheet['sources'] if 'ref' in s.keys() and 'Prophets' in Ref(s['ref']).index.categories]) > 1:
            p.append({'problem': 'more than one ref for haftara', 'url': url})
    else:
        if len([s for s in sheet['sources'] if 'ref' in s.keys() and 'Torah' in Ref(s['ref']).index.categories]) > 1:
            p.append({'problem': 'more than one ref for torah', 'url': url})
        if len([s for s in sheet['sources'] if 'ref' in s.keys() and 'Prophets' in Ref(s['ref']).index.categories]) > 1:
            p.append({'problem': 'more than one ref for neviim', 'url': url})
        if len([s for s in sheet['sources'] if 'ref' in s.keys() and 'Writings' in Ref(s['ref']).index.categories]) > 1:
            print(3333333, id)
    for source in sheet['sources']:
        if 'ref' not in source.keys() or \
                ('Prophets' in Ref(source['ref']).index.categories and day != '6') or \
                'Torah' in Ref(source['ref']).index.categories or 'Writings' in Ref(source['ref']).index.categories:
            continue
        source_text = len(re.sub('[^ א-ת]', '', source['text']['he']))
        ref_text = len(re.sub('[^ א-ת]', '', Ref(source['ref']).text('he').as_string()))
        try:
            if not (0.9 < source_text / ref_text < 1.1):
                pass
                # p.append({'problem': f'for {source["ref"]}, sheet text has length of {source_text} but Sefaria\'s text has length of {ref_text}', 'url': f'{url}.{source["node"]}',
                #           'original': f'https://hok.cauldron.sefaria.org/{source["ref"]}'})
        except ZeroDivisionError:
            p.append({'problem': f'no text in ref {source["ref"]}', 'url': f'{url}.{source["node"]}', 'original': f'https://hok.cauldron.sefaria.org/{source["ref"]}'})
    if p:
        problems.append({'problem': sheet['title']})
        problems += p
with open('problems.csv', 'w', encoding='utf-8') as fp:
    w = csv.DictWriter(fp, fieldnames=['problem', 'url', 'original'])
    w.writeheader()
    for x in problems:
        w.writerow(x)
