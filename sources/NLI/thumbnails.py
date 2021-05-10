# encoding=utf-8

import os
import re
from PIL import Image
import multiprocessing

thumb_size = 256
process_lock = multiprocessing.Lock()
# input_directory = f'./Leningrad/color'
# output_directory = f'./Leningrad/color_thumb'
input_directory = os.environ['INPUT_DIRECTORY']
try:
    output_directory = os.environ['OUTPUT_DIRECTORY']
except KeyError:
    output_directory = f'{input_directory}_thumb'
if not os.path.exists(output_directory):
    os.mkdir(output_directory)



def create_thumbnail(image_file):
    infile = os.path.join(input_directory, image_file)
    # outfile = re.sub(r'\.jpg', u'_thumbnail.jpg', infile)
    outfile = os.path.join(output_directory, image_file.replace('.jpg', '_thumbnail.jpg'))
    if os.path.exists(outfile):
        return
    im = Image.open(infile)
    height, length = im.size
    aspect_ratio = length / height
    new_h = thumb_size
    new_l = int(aspect_ratio * length)
    im.thumbnail((new_h, new_l))
    with process_lock:
        im.save(outfile)
        print(image_file)


original_files = sorted([f for f in os.listdir(input_directory) if re.search(r'(?<!thumbnail)\.jpg$', f)])
pool = multiprocessing.Pool()
pool.map(create_thumbnail, original_files)
