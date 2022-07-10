import csv
import django
django.setup()
from sefaria.model import *

with open('alts.csv', newline='') as fp:
    data = list(csv.DictReader(fp))

name = 'Thy Face I Seek'
alts = {'Topic': {'nodes':[]}}
for i, row in enumerate(data):
    comma = ',' if i < 2 else ''
    alts['Topic']['nodes'].append(
        {'nodeType': "ArrayMapNode",
        'depth': 0,
        'wholeRef': f"{name}{comma} {row['primary']}",
        'includeSections': False,
        'titles': [
            {
            'lang': "en",
            'primary': True,
            'text': f"{row['eng alt']}"
            },
            {
            'lang': "he",
            'primary': True,
            'text': f"{row['heb alt']}"
            }]})
ind = Index().load({ 'title' : 'Thy Face I Seek' })
ind.alt_structs = alts
ind.save()
