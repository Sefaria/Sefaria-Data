import csv
import django
django.setup()
from sefaria.model import *

with open('translations after manu.csv') as fp:
    data = csv.DictReader(fp)

    versions = []
    for row in data:
        if not row['text']:
            continue

        if row['versionTitle']:
            vtitle = row['versionTitle']
        tc = Ref(row['new ref']).text('en', vtitle)
        if tc.text:
            tc.text += f' {row["text"]}'
        else:
            tc.text = row["text"]
        tc.save()
