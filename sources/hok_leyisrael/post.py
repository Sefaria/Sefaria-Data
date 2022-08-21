import json
import django
django.setup()
from sources.functions import post_sheet

server = 'http://localhost:9000'
server = 'https://hok.cauldron.sefaria.org'
ids = []

for c in range(5):
    for p in range(2, 14):
        for d in range(7):
            try:
                with open(f'jsons/{c}-{p}-{6-d}.json') as fp:
                    sheet = json.load(fp)
            except FileNotFoundError:
                continue
            print(f'{c}-{p}-{6-d}')
            ids.append(post_sheet(sheet, server=server)['id'])
with open('ids.json', 'w') as fp:
    json.dump(ids, fp)
print(len(ids))
