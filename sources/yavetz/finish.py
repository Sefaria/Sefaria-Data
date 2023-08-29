import django
django.setup()
from sefaria.model import *
import csv
import re

with open('change.csv') as fp:
    changes = list(csv.DictReader(fp))

def change(text):
    for c in changes:
        if c['loc']:
            text = re.sub(f'^(<.*?>)?{re.escape(c["search"])}', rf'\1{c["replace"]}', text)
        else:
            text = text.replace(c["search"], c["replace"])
    return text

for index in IndexSet({'title': {'$regex': "^Haggahot Ya'avetz"}}):
    if 'Commentary on Minor Tractates' in index.categories:
        continue
    for segment in index.all_segment_refs():
        tc = segment.text('he', vtitle='Vilna Edition')
        tc.text = change(tc.text)
        # tc.save()
        if 'Mishnah' in index.categories:
            tref = segment.normal()
            base_tref = ':'.join(tref.split(' on ')[1].split(':')[:-1])
            link = Link({
                'refs': [tref, base_tref],
                'type': 'commentary',
                'auto': True,
                'generated_by': 'yyavetz mishnah linker'
            })
            # link.save()
    v=Version().load({'title': index.title})
