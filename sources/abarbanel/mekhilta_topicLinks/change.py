import csv
import re
import django
django.setup()
from sefaria.model import *

with open('/Users/yishaiglasner/Downloads/topic_links_segment.csv') as fp:
    data = list(csv.DictReader(fp))


def make_text(ref):
     if '-' in ref:
         a,b = ref.split('-')
         if a.split()[:-1] != b.split()[:-1] and b.split()[:-1]:
             print(2, ref)
             return ''
         ref = a + '-' + b.split()[-1]
     try:
         text = Ref(ref).text('he').text
     except:
         print(ref)
         return ''
     if isinstance(text, list):
         t = ''
         for i, seg in zip(range(Ref(ref).sections[-1], Ref(ref).toSections[-1]+1), text):
             t+= f'<{i}> {seg} '
     else:
         t=text
     return t


for row in data:
     row['aspaklaria text'] = row.pop('text')
     row['current text'] = make_text(row['ref'])
     if row['new ref']:
         row['new ref'] = row['new ref'].replace('Yishmael', 'Yishmael Beeri')
         try:
             Ref(row['new ref'])
         except:
             print(7, row['new ref'])
         else:
             row['beeri mapped text'] = make_text(row['new ref'])
             if not row['exact ref'] and len(Ref(row['new ref']).all_segment_refs()) < 4:
                 row['exact ref'] = row['new ref']
     
with open('/Users/yishaiglasner/Downloads/topic_links_manual.csv', 'w') as fp:
    w = csv.DictWriter(fp, fieldnames=list(data[0]))
    w.writeheader()
    for row in data:
        w.writerow(row)

