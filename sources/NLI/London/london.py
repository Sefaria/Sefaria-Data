# encoding=utf-8

# from concurrent.futures.thread import ThreadPoolExecutor
from PIL import Image
import requests
import time
import sys
import io
import os
import re

COMPLETED = os.environ['COMPLETED']
EXPORT = os.environ['EXPORT']
STOP = os.environ['STOP']

# COMPLETED, EXPORT, STOP = ['foo', 'bar', 'baz']

def combine_tiles_1d(images, dimension, id_name=None):
    widths, heights = zip(*(i.size for i in images))
    if dimension == 'width':
        cons, vars = heights, widths
    else:
        cons, vars = widths, heights
    if any(c != cons[0] for c in cons):
        print(f'{dimension}s are not identilcal in {id_name}: {cons}')
    total_var = sum(vars)
    max_con = max(cons)
    if dimension == 'width':
        new_im = Image.new('RGB', (total_var, max_con))
    else:
        new_im = Image.new('RGB', (max_con, total_var))

    offset = 0
    for im in images:
        if dimension == 'width':
            new_im.paste(im, (offset, 0))
            offset += im.size[0]
        else:
            new_im.paste(im, (0, offset))
            offset += im.size[1]
    return new_im

def combine_tiles_2d(tiles_array, id_name=None):
    rows = [combine_tiles_1d(row, 'width', f'{id_name}-{r}') for r, row in enumerate(tiles_array)]
    return combine_tiles_1d(rows, 'height', id_name)

def download_london_tiles(page):
    def download(url):
        r = requests.request('get', url)
        while r.status_code == 429:
            time.sleep(1)
            print('got error, retrying')
            r = requests.request('get', url)
        return r.content

    tiles = [[] for _ in range(25)]
    # tiles = []
    for m in range(25):
        # print('downloading row', m)
        # url_list = [f'http://www.bl.uk/manuscripts/Proxy.ashx?view=add_ms_27296_f{page}_files/13/{n}_{m}.jpg' for n in range(19)]
        # with ThreadPoolExecutor() as executor:
        #     responses = executor.map(download, url_list)
        # tiles.append([Image.open(io.BytesIO(response.content)) for response in responses])
        for n in range(19):
            print('downloading tile', page, n, m)
            r = requests.request('get', f'http://www.bl.uk/manuscripts/Proxy.ashx?view=add_ms_27296_f{page}_files/13/{n}_{m}.jpg')
            while r.status_code == 429:
                time.sleep(1)
                print('got error, retrying')
                r = requests.request('get', f'http://www.bl.uk/manuscripts/Proxy.ashx?view=add_ms_27296_f{page}_files/13/{n}_{m}.jpg')
            tiles[m].append(Image.open(io.BytesIO(r.content)))
    return tiles

if __name__ == '__main__':
    if os.path.exists(f'{COMPLETED}/completed.txt'):
        with open(f'{COMPLETED}/completed.txt') as fp:
            completed = (re.search(r'[^/]+$', r.rstrip()) for r in fp)
            completed = set(r.group() for r in completed if r)
            print(*completed, sep='\n')
    else:
        completed = set()
    if len(sys.argv) > 1:
        page_limit = sys.argv[1]
    else:
        page_limit = None
    for i in range(3, 74):
        if page_limit and i != page_limit:
            print('skipping page', i)
        for side in ['v', 'r']:
            file_name = f'tosefata_london_{i}{side}.jpg'
            if file_name in completed:
                print(file_name, 'already downloaded, skipping')
                continue
            else:
                print('downloading', file_name)
            thumbnail_name = file_name.replace('.jpg', '_thumbnail.jpg')
            page = f'{str(i).zfill(3)}{side}'
            tiles = download_london_tiles(page)
            page_image = combine_tiles_2d(tiles, page)
            page_image.save(f'{EXPORT}/{file_name}')
            page_image.thumbnail((256, 278))
            page_image.save(f'{EXPORT}/{thumbnail_name}')
    with open(f'{STOP}/stop', 'w') as fp:
        fp.write('')
