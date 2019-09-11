# encoding=utf-8

import os
import sys
import shutil
import requests
from PIL import Image
from threading import Lock
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from external_data import *


# feel free to change user agent string if you don't want to be me :wink:


# this should be pulled from the manifest
test_image = "FL21338459"

"""
At current settings, we have 14 requests per row with 18 rows. This will require 252 http requests per image.

Multithreading is 100% necessary here. We can either go image by image, but use concurrency within each image. Or we
can load the images concurrently, but each image is run in a single thread.

ThreadPoolExecutor will attempt to run 60 threads concurrently on my (Yoni) machine. The best utilization of
resources would then be running each image in a single thread, but loading multiple images at once. This strategy might
be trickier from a code writing perspective though.

Alternatively, I can split threads among both rows and columns. Say, 6 threads per for the image, but each row in the
image can spawn 10 threads. Not sure how this will work, but it's easy from a code perspective and should be sufficient
utilization of resources 
"""

# theoretically we should grab these values from the maxWidth/maxHeight from the "iif image information service"
image_width = 500
image_height = 500


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


def collect_tiles_for_row(image_id, row_number):
    folder = "./images/temp_row_tiles%i" % (row_number, )

    if os.path.exists(folder):
        try:
            os.rmdir(folder)
        except OSError:
            delete_images_in_temp_folder(folder)
            os.rmdir(folder)
    os.mkdir(folder)

    num_tiles = 7000 / image_width
    inputs = [{'index': x, 'cur_pos_x': x * image_width} for x in range(num_tiles)]
    cur_pos_y = image_height * row_number

    def pull_tile(tile_data):
        index, cur_pos_x = tile_data['index'], tile_data['cur_pos_x']
        url = "%s/%s/%i,%i,%i,%i/%i,%i/0/default.jpg" % (
            base_url, image_id, cur_pos_x, cur_pos_y,
            image_width, image_height, image_width, image_height
        )

        response = requests.get(url, headers=headers, stream=True)
        filename = "./images/temp_row_tiles%i/row_%i_image_%02d.jpg" % (row_number, row_number, index)

        with open(filename, "wb") as out_file:
            shutil.copyfileobj(response.raw, out_file)

    with ThreadPoolExecutor(max_workers=6) as executor:
        executor.map(pull_tile, inputs)

    combine_tiles_for_row(row_number)


def get_rows(image_id):
    cur_pos_y = 0
    # again, we should grab this from the "iif image information service"
    max_y = 9000
    row_indices = range(max_y/image_height)
    thread_lock = Lock()

    # while rowindex * image_height < max_y:

    def collect_row(rowindex):
        # this seems to miss the last row...
        # at 500px per row, this requires 18 cycles. Possible candidate for multithreading

        with thread_lock:
            print "getting row %i of %i" % (rowindex, max_y/image_height)
        collect_tiles_for_row(image_id, rowindex)

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(collect_row, row_indices)
    # map(collect_row, row_indices)


def combine_rows_for_image(image_id):
    folder = "./images/temp_stiched_rows"

    row_image_array = create_image_array_for_merging(folder)
    print row_image_array

    images = map(Image.open, row_image_array)
    widths, heights = zip(*(i.size for i in images))
    total_width = max(widths)
    max_height = sum(heights)
    new_im = Image.new('RGB', (total_width, max_height))

    y_offset = 0
    for im in images:
        new_im.paste(im, (0,y_offset))
        y_offset += im.size[1]

    filename = './images/%s.jpg' % image_id
    new_im.save(filename)

    delete_images_in_temp_folder(folder)


get_rows(test_image)
combine_rows_for_image(test_image)
