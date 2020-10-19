# encoding=utf-8
from __future__ import print_function

import re
import os
import json
import shutil
import requests
from bs4 import BeautifulSoup
from functools import partial
from urllib.parse import urlparse
from collections import defaultdict
from threading import Lock as threadLock
from concurrent.futures import ThreadPoolExecutor

import django
django.setup()

from sources.NLI.database import Database
from sefaria.model import *
from sefaria.system.exceptions import InputError

u"""
For Munich:
Url is valid within db. (supposedly...)
Parse page with BeautifulSoup
img_src = soup.find('img', attrs={"alt": "Image"})  // check that there is only 1 result here?
use urlparse on the original url (not the image source)
image_url = u'{}://{}{}'.format(parsed_url.scheme, parsed_url.netloc, image_src)

For each row:
Derive Ref (completed)?
Get image url
Map refs to image url:
    For this, we'll map images to an array of urls.
Write image to disk:
    Here we'll need to derive filenames. The first image in the array will just get the filename <Ref>.jpg Second and
    so-on will get <Ref>(II).jpg
    
With over 2000 images, we'll benefit from multithreading. We need to be careful about what parts of the code are thread
safe.

derive_ref(row) -> ref: row_url
get_image_url(ref_map) -> ref: [image_url]
    this method should have two parts: load_html & parse_html(locked)
save_image_to_disk(ref_map) -> {ref: [filename]}

we'll want to save the mappings of ref: image_url & ref: filename as json documents

Load html page with image src - open
Parse html page - locked
Load and write images - open
We could benefit by defining which methods need to be locked with a decorator.
"""

script_lock = threadLock()  # necessary for multithreading
counter = [0]


def get_rows_from_db():

    nli_db = Database()

    nli_db.cursor.execute('SELECT im.Im_File url, im.Im_Title refs FROM TblImages im '
                          'JOIN ('
                          '    SELECT Ma_ID FROM TblManuscripts ma '
                          '    JOIN TblLibraries li ON ma.Ma_LibID = li.Li_ID WHERE li.Li_ID = 8 '
                          ') man_map ON man_map.Ma_ID = im.Im_Ms')

    rows = [r for r in nli_db.cursor.fetchall()]
    ref_map = defaultdict(list)
    for r in rows:
        if r['refs'] is None:
            continue

        start, end = re.split(r'\s?-\s?', r['refs'])
        if not Ref.is_ref(start) or not Ref.is_ref(end):
            ref_map[r['refs']].append(r['url'])
        else:
            sefaria_ref = Ref(start).to(Ref(end)).normal()
            ref_map[sefaria_ref].append(r['url'])
    return ref_map


def get_image_url(page_url_mapping, image_urls, ref_key):
    with script_lock:
        page_url_list = page_url_mapping[ref_key]

    for page_url in page_url_list:
        page_html = requests.get(page_url).text

        with script_lock:
            soup = BeautifulSoup(page_html, 'html5lib')
            img_src = soup.find('img', attrs={"alt": "Image"})['src']
            img_src = re.sub('images', 'images/200', img_src)

            parsed_url = urlparse(page_url)
            image_urls[ref_key].append(u'{}://{}{}'.format(parsed_url.scheme, parsed_url.netloc, img_src))

    with script_lock:
        count = counter[0]
        if count % 20 == 0:
            print(count)
        counter[0] = count + 1

    return


def write_image_to_file(image_url_mapping, file_mapping, tref):
    with script_lock:
        url_list = image_url_mapping[tref]
    for i, image_url in enumerate(url_list):
        if i == 0:
            filename = u'munich_images/{}.jpg'.format(tref)
        else:
            filename = u'munich_images/{}({}).jpg'.format(tref, u'I'*i)

        with script_lock:
            file_mapping.append({
                'full_ref': tref,
                'expaned_refs': [q.normal() for q in Ref(tref).all_segment_refs()],
                'image_file': filename,
                'Manuscript': 'Munich'
            })

        if not os.path.exists(filename):
            print(f'downloading ${filename}')
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(filename, 'wb') as fp:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, fp)

    with script_lock:
        count = counter[0]
        if count % 20 == 0:
            print(count)
        counter[0] = count + 1
    return


if __name__ == '__main__':
    html_map, image_map, file_map = get_rows_from_db(), defaultdict(list), []

    get_image_url_p = partial(get_image_url, html_map, image_map)
    write_image_to_file_p = partial(write_image_to_file, image_map, file_map)

    with ThreadPoolExecutor() as executor:
        executor.map(get_image_url_p, html_map.keys())

    counter[0] = 0
    print("Finished collecting html. Starting to assemble images")

    with ThreadPoolExecutor() as executor:
        executor.map(write_image_to_file_p, image_map.keys())

    with open('munich_filemap.json', 'w') as fp:
        json.dump(file_map, fp)
