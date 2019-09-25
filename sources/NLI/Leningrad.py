# encoding=utf-8

import re
import os
import json
from bs4 import BeautifulSoup
from multiprocessing import Pool
from multiprocessing import Lock as proceesLock
from pdf2image import convert_from_path

import django
django.setup()
from sefaria.model import *


"""
Basic concept:
For image conversions, first configure the output filename. If the file doesn't exist, convert.
We'll want two conversions: 500dpi and 100dpi at 512px.
Filenames - same filename with the extension changed to jpg. For thumbnails, add _thumbnail before extension

Images can be downloaded from http://www.tanach.us/LCFolios/LC_Folios.zip
Archive contains the index used to map images to refs
"""

process_lock = proceesLock()
current_file = [0]


def convert_file(input_filename, input_dir='./Leningrad/pdf', output_dir='./Leningrad/jpg'):
    output_filename = os.path.join(output_dir, re.sub(ur'pdf$', ur'jpg', input_filename))
    thumb_filename = os.path.join(output_dir, re.sub(ur'\.pdf$', ur'_thumbnail.jpg', input_filename))

    full_file = os.path.join(input_dir, input_filename)

    if not os.path.exists(output_filename):
        pages = convert_from_path(full_file, fmt='JPEG', dpi=500)
        if len(pages) > 1:
            with process_lock:
                print u"multiple pages found at file {}".format(input_filename)
        page = pages[0]
        page.save(output_filename)

    if not os.path.exists(thumb_filename):
        page = convert_from_path(full_file, fmt='JPEG', dpi=100, size=512)[0]
        page.save(thumb_filename)

    with process_lock:
        current_file[0] += 1
        file_num = current_file[0]
        print "finished file {} / {}".format(file_num, total_files)


def generate_file_mapping():
    def resolve_ref(td_list):
        book = td_list[1].text
        sections = re.sub(ur'[a-z]', u'', td_list[2].text)

        full_tref = u'{} {}'.format(book, sections)
        if not Ref.is_ref(full_tref):
            print "could not resolve Ref for Page ID {}".format(td_list[0].text)

        return Ref(full_tref).normal()

    with open('./Leningrad/LCIndex.html') as fp:
        soup = BeautifulSoup(fp, 'html5lib')

    table = soup.table
    rows = [r.find_all('td') for r in table.find_all('tr')]
    ref_rows = [r for r in rows if len(r) == 4]

    image_data = {}
    for row in ref_rows:
        data_key = 'LC_Folio_{}.jpg'.format(row[0].text)
        if data_key in image_data:
            image_data[data_key] += u'; {}'.format(resolve_ref(row))
        else:
            image_data[data_key] = resolve_ref(row)

    return image_data


with open('Leningrad_map.json', 'w') as fp:
    json.dump(generate_file_mapping(), fp)

# file_list = [os.path.join('./Leningrad/pdf', f) for f in os.listdir('./Leningrad/pdf/')]
file_list = os.listdir('./Leningrad/pdf/')
total_files = len(file_list)
pool = Pool()
pool.map(convert_file, file_list)




