import requests
import os
from PIL import Image
import io

for n in list(range(1,295)):
    for side in ['r', 'v']:
        if 187 < n < 190 or (n == 163 and side == 'r') or n == 197 or (n == 91 and side == 'v'): #why these pages are missing. mikraot gdolot haketer have all (maybe from other photographing)
            continue
        if n < 93:
            i = (n-3) // 10 + 2
        elif n < 100:
            i = 11
        elif n < 140:
            i = n // 10 + 2
        elif n < 188:
            i = (n+2) // 10 + 2
        elif n < 196:
            i = 21
        elif n < 241:
            i = (n-1) // 10 + 3
        else:
            i = (n+2) // 10 + 3

        if (side == 'r' and (n == 93 or n == 100)) or n == 201:
            i -= 1
        elif n == 228 and side == 'r':
            n = 2238

        delim = '.' if n == 2 and side == 'v' else '' if n == 152 and side == 'v' else '-'

        if n ==110:
            side = side.capitalize()

        url = f'https://barhama.com/ajaxzoom/pic/AleppoWM/{i}-{n}{delim}{side}_photo_by_Ardon_Bar-Hama.jpg'
        if n == 2238:
            n = 228
        fname = f'images/aleppo_{i}-{n}-{side}.jpg'
        nthumb = f'images/aleppo_{i}-{n}-{side}_thumbnail.jpg'
        if os.path.isfile(fname) and os.path.isfile(nthumb):
            continue
        r = requests.request('get', url)
        if r.status_code != 200:
            url = f'https://barhama.com/ajaxzoom/pic/AleppoWM/{i}-{n}{delim}{side}x_photo_by_Ardon_Bar-Hama.jpg'
            r = requests.request('get', url)
            if r.status_code != 200:
                print(f'error {r.status_code} for url: {url}')
                continue
        if not os.path.isfile(fname):
            with open(fname, 'wb') as fp:
                fp.write(r.content)
        if not os.path.isfile(nthumb):
            thumb = Image.open(io.BytesIO(r.content))
            thumb.thumbnail((256, 278))
            thumb.save(nthumb)
