# encoding=utf-8

import os
import re
import time
import json
import codecs
import shutil
import requests
from PIL import Image
from requests import ConnectTimeout
from requests.exceptions import ReadTimeout
from urllib3.exceptions import ReadTimeoutError
from threading import Lock as ThreadLock
from sources.functions import weak_connection
from functools import partial
from sources.NLI.database import Database
from concurrent.futures import ThreadPoolExecutor
from sources.NLI.Vienna.external_data import *

import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError


def get_manifest_canvases():
    with open('vienna_manifest.json') as fp:
        manifest = json.load(fp)
    # response = requests.get(manifest_url, headers=headers)
    # manifest = response.json()
    # manifest = json.loads(manifest['Value'])
    return manifest['sequences'][0]['canvases']


# theoretically we should grab these values from the maxWidth/maxHeight from the "iif image information service"
# image_width = 500
# image_height = 500


def create_image_array_for_merging(folder):
    row_image_array = []
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        row_image_array.append(file_path)
    row_image_array.sort()
    return row_image_array


def delete_images_in_temp_folder(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        os.unlink(file_path)


def combine_tiles_for_row(row_number):
    folder = "./images/temp_row_tiles{}".format(row_number)

    row_image_array = create_image_array_for_merging(folder)

    images = map(Image.open, row_image_array)
    widths, heights = zip(*(i.size for i in images))
    total_width = sum(widths)
    max_height = max(heights)
    new_im = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset,0))
        x_offset += im.size[0]

    filename = './images/temp_stiched_rows/%02d.jpg' % row_number
    new_im.save(filename)

    delete_images_in_temp_folder(folder)
    os.rmdir(folder)


def collect_tiles_for_row(image_data, row_number):
    folder = "./images/temp_row_tiles%i" % (row_number, )
    image_id = image_data['image_id']
    tile_width, tile_height = image_data['tile_width'], image_data['tile_height']

    if os.path.exists(folder):
        try:
            os.rmdir(folder)
        except OSError:
            delete_images_in_temp_folder(folder)
            os.rmdir(folder)
    os.mkdir(folder)

    max_x = image_data['max_width']
    num_tiles = max_x / tile_width
    inputs = [{'index': x, 'cur_pos_x': x * tile_width} for x in range(num_tiles)]
    cur_pos_y = tile_height * row_number

    @weak_connection
    def pull_tile(tile_data):
        index, cur_pos_x = tile_data['index'], tile_data['cur_pos_x']
        url = "%s/%s/%i,%i,%i,%i/%i,%i/0/default.jpg" % (
            base_url, image_id, cur_pos_x, cur_pos_y,
            tile_width, tile_height, tile_width, tile_height
        )

        response = requests.get(url, headers=headers, stream=True)
        filename = "./images/temp_row_tiles%i/row_%i_image_%02d.jpg" % (row_number, row_number, index)

        with open(filename, "wb") as out_file:
            shutil.copyfileobj(response.raw, out_file)

    with ThreadPoolExecutor(max_workers=6) as executor:
        executor.map(pull_tile, inputs)

    combine_tiles_for_row(row_number)


def prepare_tiles_for_row(image_data, row_number):
    image_data['row_number'] = row_number
    folder = "./images/temp_row_tiles%i" % (row_number,)

    if os.path.exists(folder):
        try:
            os.rmdir(folder)
        except OSError:
            delete_images_in_temp_folder(folder)
            os.rmdir(folder)
    os.mkdir(folder)

    tile_width, tile_height = image_data['tile_width'], image_data['tile_height']
    max_x = image_data['max_width']
    num_tiles = max_x / tile_width
    inputs = [{
        'index': x,
        'cur_pos_x': x * tile_width,
        'cur_pos_y': tile_height * row_number,
    } for x in range(num_tiles)]

    for thing in inputs:
        thing.update(image_data)
    return inputs


# @weak_connection
def pull_tile(tile_data, attempt=0):
    index, cur_pos_x = tile_data['index'], tile_data['cur_pos_x']
    url = "%s/%s/%i,%i,%i,%i/%i,%i/0/default.jpg" % (
        base_url, tile_data['image_id'], tile_data['cur_pos_x'], tile_data['cur_pos_y'],
        tile_data['tile_width'], tile_data['tile_height'], tile_data['tile_width'], tile_data['tile_height']
    )

    with global_lock:
        tile_num[0] += 1
        print(tile_num[0])
        if tile_num[0] % 20 == 0:
            print('\n')

    for _ in range(10):
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=2)
            break
        except (ConnectTimeout, ReadTimeoutError, ReadTimeout):
            with global_lock:
                print("Retrying connection")
    else:
        raise ConnectTimeout

    filename = "./images/temp_row_tiles%i/row_%i_image_%02d.jpg" % (tile_data['row_number'], tile_data['row_number'],
                                                                    index)
    tile_data['filename'] = filename

    with global_lock:
        with open(filename, "wb") as out_file:
            shutil.copyfileobj(response.raw, out_file)

    try:
        Image.open(filename)
    except IOError:
        if attempt > 9:
            raise IOError
        pull_tile(tile_data, attempt=attempt+1)


def download_image(image_data):
    tile_num[0] = 0
    max_y = image_data['max_height']
    row_indices = range(max_y / image_data['tile_height'])

    tile_data = []
    for row_num in row_indices:
        tile_data.extend(prepare_tiles_for_row(image_data, row_num))

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(pull_tile, tile_data)

    # make sure all images have been downloaded properly
    while True:
        success = True

        for tile in tile_data:
            try:
                Image.open(tile['filename'])
            except IOError:
                print("attempting to re-pull tile")
                success = False
                pull_tile(tile)
        if success:
            break

    for row in row_indices:
        combine_tiles_for_row(row)


def get_rows(image_data):

    image_id = image_data['image_id']
    max_y = image_data['max_height']

    # this seems to miss the last row...
    row_indices = range(max_y/image_data['tile_height'])
    # thread_lock = Lock()

    def collect_row(rowindex):

        # with thread_lock:
        #     print "getting row %i of %i" % (rowindex, max_y/image_data['tile_height'])
        collect_tiles_for_row(image_data, rowindex)

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(collect_row, row_indices)
    # map(collect_row, row_indices)


def combine_rows_for_image(image_dict):
    folder = "./images/temp_stiched_rows"

    row_image_array = create_image_array_for_merging(folder)
    # print row_image_array

    images = map(Image.open, row_image_array)
    widths, heights = zip(*(i.size for i in images))
    total_width = max(widths)
    max_height = sum(heights)
    new_im = Image.new('RGB', (total_width, max_height))

    y_offset = 0
    for im in images:
        new_im.paste(im, (0,y_offset))
        y_offset += im.size[1]

    if isinstance(image_dict['image_ref'], str):
        filename = u'./images/{}.jpg'.format(image_dict['image_ref'])
    else:
        filename = u'./images/{}.jpg'.format(u' - '.join(image_dict['image_ref']))
    new_im.save(filename)

    delete_images_in_temp_folder(folder)


global_lock = ThreadLock()
image_num, tile_num = [0], [0]


@weak_connection
def collect_image_dimensions(image_data, weak_network=True):
    image_info_url = image_info_url_template.format(image_data['image_id'])
    response = requests.get(image_info_url, headers=headers, timeout=5)
    remote_image_data = response.json()

    image_data['max_height'], image_data['max_width'] = remote_image_data['height'], remote_image_data['width']

    tile_dimensions = remote_image_data['sizes'][-1]
    image_data['tile_height'], image_data['tile_width'] = tile_dimensions['height'], tile_dimensions['width']

    with global_lock:
        image_num[0] += 1
        print("loaded image data for image {}".format(image_num[0]))


def bulk_image_dimensions(image_data_list):
    with ThreadPoolExecutor() as executor:
        executor.map(collect_image_dimensions, image_data_list)
    # map(collect_image_dimensions, image_data_list)


def derive_label_from_row(row_data):
    filename = row_data['Im_File']
    label = re.search(r'\\0*(\d+[rv])\.jpg$', filename).group(1)
    return 'fol. {}'.format(label.zfill(4))


def derive_ref_from_row(row_data):
    mapping = {
        u'נידה': u'נדה',
        u'מקואות': u'מקוואות',
        u'עוקצים': u'עוקצין'
    }

    tref = re.sub(u'|'.join(mapping.keys()), lambda x: mapping[x.group()], row_data['Im_Title'])

    raw_split = re.split(r'\s*-\s*', tref)
    if len(raw_split) != 2:
        with codecs.open('bad_refs.txt', 'a', 'utf-8') as fp:
            fp.write(u'{}\n'.format(row_data['Im_Title']))
        return row_data['Im_Title']

    start, end = raw_split

    try:
        return Ref(u'{} {}'.format(u'תוספתא', start)).normal(), Ref(u'{} {}'.format(u'תוספתא', end)).normal()
    except InputError as error:
        with codecs.open('bad_refs.txt', 'a', 'utf-8') as fp:
            fp.write(u'{}\n{}\n\n'.format(row_data['Im_Title'], error))
        return row_data['Im_Title']


"""
Still need to do:
We'll want to compile some data about each image:
{
    image_id,
    image_ref,
    image_information_url,  # can be derived from image_id
    tile_height,
    tile_width,
    max_height,
    max_width
}

height and width values require an http request. We'll want to write a method that takes an image dict and loads the
appropriate image data. We can then assemble a list of these dictionaries and collectively fetch all the data with one
ThreadPoolExecutor

As far as the Ref data is concerned, I believe all the relevant information is in the TblImages table. We'll want to
make sure the start_ref and end_ref is parsable. We can match db data to manifest data using the image labels.

Write a method that loads the image data, then use that data to test that the script still works. We can then work
to scale that up to the whole manifest.

Assuming no erros, it could still take over 3 hours to collect the who set. Two things should help:
1) use the weak network decorator
2) search through any images that have already been downloaded and purge them from list of images to be retrieved. 
This will mean that a failed run won't be wasted.

Now write a function that will pull labels out from the image table
"""

if __name__ == '__main__':
    if os.path.exists('bad_refs.txt'):
        os.remove('bad_refs.txt')
    db = Database()
    db.cursor.execute('SELECT Im_File, Im_Title FROM TblImages WHERE Im_Ms = 7658 AND Im_Title NOT NULL')
    rows = db.cursor.fetchall()
    image_data = {derive_label_from_row(r): derive_ref_from_row(r) for r in rows}
    # sys.exit(0)
    try:
        os.mkdir('images/temp_stiched_rows')
    except OSError:
        delete_images_in_temp_folder('images/temp_stiched_rows')

    canvases = get_manifest_canvases()

    full_image_data = [{
        'image_id': im['images'][0]['@id'], 'image_ref': image_data[im['label']]
    } for im in canvases if im['label'] in image_data]

    for im in full_image_data:
        image_file = u'./images/{}.jpg'.format(u' - '.join(im['image_ref']))
        if os.path.exists(image_file):
            if isinstance(im['image_ref'], str):
                os.rename(image_file, u'./images/{}.jpg'.format(im['image_ref']))
            else:
                os.rename(image_file, u'./images/{}.jpg'.format(u' - '.join(im['image_ref'])))

    # with ThreadPoolExecutor() as executor:
    #     executor.map(collect_image_dimensions, image_id_list)
    # map(collect_image_dimensions, test_images)
    bulk_image_dimensions(full_image_data)

    for i, im in enumerate(full_image_data):
        if isinstance(im['image_ref'], str):
            correct_image_file = u'./images/{}.jpg'.format(im['image_ref'])
        else:
            correct_image_file = u'./images/{}.jpg'.format(u' - '.join(im['image_ref']))

        successful_download = False
        while not successful_download:

            print('\nimage {}: {}\n'.format(i, im['image_ref']))
            if os.path.exists(correct_image_file):
                successful_download = True
                continue

            try:
                download_image(im)
                combine_rows_for_image(im)
            except IOError:
                print("attempting to download image {} again".format(i))
            else:
                successful_download = True

        # break

    os.rmdir('images/temp_stiched_rows')
