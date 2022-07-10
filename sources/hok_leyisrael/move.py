import json
import requests
import django
django.setup()
from sources.functions import post_sheet
from sefaria.model import *

dest = 'https://www.sefaria.org'
orig = 'https://hok.cauldron.sefaria.org'
with open('ids.json') as fp:
    ids = json.load(fp)[27:]
with open('new_ids.json') as fp:
    new_ids = json.load(fp)
sheets = []
new_ids = []

# ens = ['Bechukotai']*7 + ['Chukat']*7 + ['Pinchas']*7
# missing_slugs = ['parashat-chukat']*7 + ['parashat-pinchas']*7

problem = False
for i in ids:
    req = requests.get(f'{orig}/api/sheets/{i}')
    if req.status_code != 200:
        print('probllem with', i)
        problem = True
        break

    sheet = req.json()
    # for source in sheet['sources']:
    #     try:
    #         source['text']['en'] = source['text']['en'].replace(' . ', ' ')
    #     except KeyError:
    #         pass
    sheet.pop('owner')
    sheet.pop('id')
    sheet.pop('_id')

    # par = sheet.pop('tags')[0]
    # topic = Topic().load({'titles.text': par, 'slug': {'$regex': '^parashat'}})
    # if topic:
    #     slug = topic.slug
    # else:
    #     slug = missing_slugs.pop(0)
    # term = Term().load({'scheme': 'Parasha', 'titles.text': par})
    # if term:
    #     en = term.name
    # else:
    #     en = ens.pop(0)
    # sheet['topics'] = [{'slug': slug, 'asTyped': en, 'en': en, 'he': par}]

    sheets.append(sheet)

if not problem:
    for sheet in sheets:
        new_ids.append(post_sheet(sheet, server=dest)['id'])
        with open('new_ids.json', 'w') as fp:
            json.dump(new_ids, fp)
print(len(new_ids))
