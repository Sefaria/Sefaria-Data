import csv
import re
import django
django.setup()
from sefaria.model import *

with open('asups.csv') as fp:
    data = list(csv.DictReader(fp))

for row in data:
    pl = 'BDB Dictionary' if len(row['rid']) == 6 else 'BDB Aramaic Dictionary'
    le = LexiconEntry().load(({'parent_lexicon': pl, 'headword': row['hw']}))
    if not le:
        # print(pl, row['rid'], row['hw'])
        continue
    text = le.content['senses'][0]['definition'].strip()
    prev = re.escape(f'{row["prevprev"]}')
    if not prev.endswith('strong>'):
        prev += re.escape(row["prev"])
    if not re.search('strong> *$', prev):
        prev = re.sub(r'(\\ *)$', r'</strong>\1', prev, 1)
    ref = re.escape(row['sup'].strip())
    if re.search(f'{prev} *<sup', text):
        print(11111)
    sups = re.findall(f'{prev} *<a[^>]*>{ref}</a>', text)
    if len(sups) == 1:
        print(11111)
