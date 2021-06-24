import requests
import csv
from os.path import expanduser
from PIL import Image

with open(f'{expanduser("~")}/Downloads/aggregation.csv', newline='', encoding='utf-8') as fp:
    data = csv.DictReader(fp)
    data = {int(r['im run']) for r in data if r['description']=='כתב יד וינה Heb. 20'}
    print(sorted({x for x in range(451,660)}-data))

for i in range(6,7):#, 449):
    r = requests.request('get', f'https://content.staatsbibliothek-berlin.de/dms/PPN666097402/1200/0/00000{str(i).zfill(3)}.jpg')
    if r.status_code != 200:
        print(f'failed to download page {i}. code {r.status_code}')
    else:
        file = f'tossefta_erfurt_{i-3}.jpg'
        with open(f'tossefta_erfurt_{i-3}.jpg', 'wb') as fp:
            fp.write(r.content)
        try:
            im = Image.open(file)
            im.thumbnail((256, 278))
            im.save(f'thumb_{file}', "JPEG")
        except IOError:
            print("cannot create thumbnail for", file)
