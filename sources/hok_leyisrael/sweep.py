import django
django.setup()
from sefaria.model import *
import requests

base = 'http://raktora.50webs.com/hokleisrael/'
add = ['lehlecha', 'hsara', 'itro', 'teroma', 'tetzave', 'pikuday', 'aharey', 'bahar', 'behukotay', 'behaaloteha', 'hukat', 'masey', 'ekev', 'ree', 'kiteze', 'vayeleh', 'haazino', 'habracha']
for parasha in TermSet({'category': 'Torah Portions'})[:54] + add:
    if type(parasha) != str:
        titles = [t['text'].replace(' ', '') for t in parasha.titles if t['lang'] == 'en']
        titles += [t.replace('y', '') for t in titles]
        titles += [t.replace('ch', 'h') for t in titles]
    else:
        titles = [parasha]
    for title in titles:
        title = title.lower()
        req = requests.request('get', f'{base}{title}.htm')
        if req.status_code == 200:
            break
    if req.status_code != 200:
        print(title, req.status_code)
        continue
    else:
        open(f'data/{title}.html', 'wb').write(req.content)


