import json
import requests
from bs4 import BeautifulSoup

for i in range(8675, 9000):
    page = requests.get(f'https://mg.alhatorah.org/MikraotGedolot/lexicon/lexicon.php/B{i}')
    if page.status_code != 200:
        print('error', i)
        continue
    j = page.json()
    if 'BDB' in j:
        with open(f'alhatorah/{i}.json', 'w') as fp:
            json.dump(j, fp)
