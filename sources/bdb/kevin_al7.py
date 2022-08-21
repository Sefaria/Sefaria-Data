import csv
import json
import django
django.setup()
from sefaria.model import *

with open('hub_dict_new.json') as fp:
    HUB_DICT = json.load(fp)
with open('kev_dict.json') as fp:
    KEV_DICT = json.load(fp)

def push_entry(rid, hw, old_content=None, new_content='', pre=''):
    rid = int(rid)
    prev = rid
    next = rid + 1
    while True:
        le = LexiconEntry().load({'parent_lexicon': {'$regex': 'BDB.*?Dictionary'}, 'rid': str(prev)})
        if le:
            le.next_hw = hw
            if old_content:
                le.content['senses'][0]['definition'] = old_content
            le.save()
            prev = le.headword
            parent = le.parent_lexicon
            break
        prev -= 1
    while True:
        le = LexiconEntry().load({'parent_lexicon': {'$regex': 'BDB.*?Dictionary'}, 'rid': str(next)})
        if le:
            le.prev_hw = hw
            le.save()
            next_hw = le.headword
            break
        next += 1
    cur = rid + 1
    lel = []
    while True:
        le = LexiconEntry().load({'parent_lexicon': {'$regex': 'BDB.*?Dictionary'}, 'rid': str(cur)})
        if le:
            cur += 1
            le.rid = str(cur)
            lel.append(le)
        else:
            break
    for le in lel:
        le.save()
    le = LexiconEntry({'headword': hw,
                       'parent_lexicon': parent,
                       'content': {'senses': [{'definition': new_content}]},
                       'rid': str(rid+1),
                       'quotes': [],
                       'next_hw': next_hw,
                       'prev_hw': prev,
                       'pre_headword': pre})
    le.save()
    return cur - 1

def push_dicts(start, last):
    for i in range(last, start-1, -1):
        try:
            parent = 'BDB Dictionary'
            hub = KEV_DICT[f'{parent}_{i}']['hub']
        except KeyError:
            parent = 'BDB Aramaic Dictionary'
            hub = KEV_DICT[f'{parent}_{i}']['hub']
        if hub:
            HUB_DICT[hub]['kevin'] = f'{parent}_{i+1}'
        KEV_DICT[f'{parent}_{i+1}'] = {'hub': hub}
        KEV_DICT.pop(f'{parent}_{i}')

def push_and_treat_dicts(kev, hub, hw, old_content=None, new_content='', pre=''):
    parent, rid = kev.split('_')
    last = push_entry(rid, hw, old_content, new_content, pre)
    push_dicts(int(rid)+1, last)
    kev = kev.replace(rid, str(int(rid)+1))
    try:
        HUB_DICT[hub]['kevin'] = kev
    except KeyError:
        HUB_DICT[hub] = {'kevin': kev}
    KEV_DICT[kev] = {'hub': hub}

if __name__ == '__main__':
    with open('split.csv', newline='') as fp:
        data = list(csv.DictReader(fp))
    data.sort(key=lambda x: int(x['after'].split('_')[1]))
    data.reverse()
    for row in data:
        row = {k: v.strip() for k, v in row.items()}
        print(f"adding the entry {row['hw']} after {row['after']}")
        push_and_treat_dicts(row['after'], row['hub'], row['hw'], row['con1'], row['con2'], row['pre'])
        if row['new']:
            HUB_DICT[row['hub']]['type'] = 'new from add'
        elif 'type' not in HUB_DICT[row['hub']]:
            HUB_DICT[row['hub']]['type'] = 'regular'

    # with open('hub_dict_try.json', 'w') as fp:
    #     json.dump(HUB_DICT, fp)
    # with open('kev_dict_try.json', 'w') as fp:
    #     json.dump(KEV_DICT, fp)
