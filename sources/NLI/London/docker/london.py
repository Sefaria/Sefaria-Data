from PIL import Image
import requests
import time
import io

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
    tiles = [[] for _ in range(25)]
    for m in range(25):
        for n in range(19):
            r = requests.request('get', f'http://www.bl.uk/manuscripts/Proxy.ashx?view=add_ms_27296_f{page}_files/13/{n}_{m}.jpg')
            while r.status_code == 429:
                time.sleep(1)
                r = requests.request('get', f'http://www.bl.uk/manuscripts/Proxy.ashx?view=add_ms_27296_f{page}_files/13/{n}_{m}.jpg')
            tiles[m].append(Image.open(io.BytesIO(r.content)))
    return tiles

if __name__ == '__main__':
    for i in range(3, 74):
        for side in ['v', 'r']:
            page = f'{str(i).zfill(3)}{side}'
            tiles = download_london_tiles(page)
            page_image = combine_tiles_2d(tiles, page)
            page_image.save(f'./london_images/tosefata_london_{i}{side}.jpg')
            page_image.thumbnail((256, 278))
            page_image.save(f'./london_images/tosefata_london_{i}{side}_thumbnail.jpg')
