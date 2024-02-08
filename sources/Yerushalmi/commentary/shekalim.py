import csv

import django
django.setup()
from sefaria.model import *
import json

def mefaresh(mefaresh):
    data = []

    with open('mapping_shekalim.json') as fp:
        mapping = json.load(fp)
    mapping['Jerusalem Talmud Shekalim 1:1:50'] = mapping['Jerusalem Talmud Shekalim 1:1:50'][:-3]
    mapping['Jerusalem Talmud Shekalim 2:3:23'] = mapping['Jerusalem Talmud Shekalim 2:3:23'][:-2]
    mapping['Jerusalem Talmud Shekalim 4:3:2'] = 'JTmock Shekalim 4:3:3'
    mapping['Jerusalem Talmud Shekalim 4:4:38'] = 'JTmock Shekalim 4:4:8'
    mapping['Jerusalem Talmud Shekalim 5:1:10'] = 'JTmock Shekalim 5:1:3'
    mapping['Jerusalem Talmud Shekalim 6:1:9'] = 'JTmock Shekalim 6:1:4'
    mapping['Jerusalem Talmud Shekalim 7:3:27'] = 'JTmock Shekalim 7:3:6'
    mapping['Jerusalem Talmud Shekalim 4:4:49'] = mapping['Jerusalem Talmud Shekalim 4:4:49'][:-3]
    mapping['Jerusalem Talmud Shekalim 5:4:18'] = mapping['Jerusalem Talmud Shekalim 5:4:18'][:-3]
    mapping['Jerusalem Talmud Shekalim 8:3:9'] = mapping['Jerusalem Talmud Shekalim 8:3:9'][:-2]

    prev = 'JTmock Shekalim 1:1:1'
    for segment in Ref(f'{mefaresh} on Jerusalem Talmud Shekalim').all_segment_refs():
        links = [l for l in segment.linkset() if l.generated_by == 'moved from old Yerushalmi links']
        if len(links) == 1:
            ref = [r for r in links[0].refs if Ref(r).book == 'JTmock Shekalim'][0]
            '''new_ref = mapping[ref]
            if segment.normal() in ['Penei Moshe on Jerusalem Talmud Shekalim 4:4:45', 'Korban HaEdah on Jerusalem Talmud Shekalim 4:4:46', 'Korban HaEdah on Jerusalem Talmud Shekalim 4:4:47']:
                new_ref = 'JTmock Shekalim 4:4:7'
            elif segment.normal() in ['Korban HaEdah on Jerusalem Talmud Shekalim 5:4:41', 'Korban HaEdah on Jerusalem Talmud Shekalim 5:4:42', 'Korban HaEdah on Jerusalem Talmud Shekalim 5:4:43']:
                new_ref = 'JTmock Shekalim 5:4:10'''
            if '-' in ref:
                print(1111, ref, segment)
        else:
            print('number of links is', len(links), segment.text('he').text)
            if 'הדרן עלך' not in segment.text('he').text and 'סליק' not in segment.text('he').text:
                ref = ''
        if not ref:
            problem = 'empty'
        elif prev and Ref(prev).follows(Ref(ref)):
            problem = 'sequence'
        else:
            problem = ''
        data.append({'content': segment.text('he').text, 'base text ref': ref, 'problem': problem})
        prev = ref
    return data

if __name__ == '__main__':
    for com in ['Penei Moshe', 'Korban HaEdah']:
        data = mefaresh(com)
        with open(f'{com} Shekalim.csv', 'w', encoding='utf-8', newline='') as fp:
            w = csv.DictWriter(fp, fieldnames=['content', 'base text ref', 'problem'])
            w.writeheader()
            for item in data:
                w.writerow(item)
