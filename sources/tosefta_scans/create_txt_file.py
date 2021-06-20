import django
django.setup()
from sefaria.model import *
import re

text = []
for seder in ['Zeraim', 'Moed', 'Nashim', 'Nezikin', 'Chullin']:
    if seder == 'Chullin':
        inds = [library.get_index('Tosefta Chullin')]
    else:
        inds = library.get_indexes_in_category(['Tosefta', 'Lieberman Edition', f'Seder {seder}'], full_records=True)
        inds = list(inds)
        inds.sort(key=lambda x: x.order)
    for index in inds:
        text.append('\n'+index.get_title('he'))
        for n, chapter in enumerate(Ref(index.title).text('he').text, 1):
            text.append(f'\nפרק {n}\n')
            text += [f"{re.sub('<.*?>', '', h)}L" for h in chapter]
with open('lieberman.txt', 'w', encoding='utf-8') as fp:
    fp.write('\n'.join(text))
