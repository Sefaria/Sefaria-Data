import csv
import json
import django
django.setup()
from sefaria.model import *
from sefaria.utils.talmud import section_to_daf

with open('map_old_to_new-new.json') as fp:
    mapping = json.load(fp)
with open('translations.json') as fp:
    texts = json.load(fp)

I = 0

def convert_text(text):
    global I
    segments = []
    for v, vol in enumerate(text['chapter'], 1):
        for p, page in enumerate(vol, 1):
            daf = section_to_daf(p)
            for s, seg in enumerate(page, 1):
                if seg:
                    range = ''
                    old = f'Zohar old {v}:{daf}:{s}'
                    if old in mapping and mapping[old]:
                        new = mapping[old].replace(' TNNNG', '')
                        if len(Ref(new).all_segment_refs()) > 1:
                            # print('range',new)
                            range = 'range'
                    else:
                        new = ''
                        I += 1
                        # print('no mapping', old)
                    segments.append({
                        'old ref': old,
                        'text': seg,
                        'old hebrew': Ref(old).text('he').text,
                        'new ref': new,
                        'range': range,
                        'new text': Ref(new).text('he').text if new else '',
                        'versionTitle': text['versionTitle'],
                        'versionSource': text['versionSource']
                    })
    refs = [x['old ref'] for x in segments]
    for x in refs:
        if refs.count(x) != 1:
            print(x)
    return segments


segments = []
for text in texts:
    segments += convert_text(text)
segments.sort(key=lambda x: Ref(x['old ref']).sections)
new = []
for row in segments:
    new.append(row)
    if row['range']:
        refs = Ref(row['new ref']).all_segment_refs()
        new += [{} for _ in range(len(refs)-1)]
        for r in new[-len(refs):]:
            r['range'] = 'range'
            r['new ref'] = refs.pop(0).normal()
            r['new text'] = Ref(r['new ref']).text('he').text
with open('translations.csv', 'w') as fp:
    w = csv.DictWriter(fp, fieldnames=['old ref', 'text', 'old hebrew', 'new ref', 'range', 'new text', 'versionTitle', 'versionSource'])
    w.writeheader()
    for row in new:
        w.writerow(row)

print(I)
