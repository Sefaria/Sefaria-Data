import re
import csv
import django
django.setup()
from sefaria.model import *

with open('samaritan - samaritan.csv') as fp:
    data = list(csv.DictReader(fp))

for row in data:
    les = LexiconEntrySet({'headword': row['headword'], 'rid': row['rid']})
    if len(les) != 1:
        print(1111)
        continue
    le = les[0]
    text = le.content['senses'][0]['definition']
    sams = re.findall('(.{,10})(?:<span dir="rtl">)?~(.*?)~(?:</span>)?(.{,10})', row['text'])
    if not sams:
        print(1.5, row['headword'])
    for before, sam, after in sams:
        before, after = re.escape(before), re.escape(after)
        if len(sam) > 10:
            print(2222, sam)
        matches = re.findall(f'{before}(?:<span dir="rtl">)?.*?(?:</span>)?{after}', text)
        if len(matches) != 1:
            print(3333)
        new = ''.join(dict(zip("אבגדהוזחטיכלמנסעפצקרשת", "ࠀࠁࠂࠃࠄࠅࠆࠇࠈࠉࠊࠋࠌࠍࠎࠏࠐࠑࠒࠓࠔࠕ")).get(c, c) for c in sam)
        text = re.sub(f'({before})(?:<span dir="rtl">)?.*?(?:</span>)?({after})', r'\1<span class="samaritan">{}</span>\2'.format(new), text)
    le.content['senses'][0]['definition'] = text
    # print(le.content['senses'][0]['definition'])
    le.save()
