# coding=utf8
import django

django.setup()

import os
import csv
import re
import requests
from bs4 import BeautifulSoup
import PIL
from PIL import Image
from io import BytesIO
from base64 import b64decode, b64encode
import statistics
import bleach

from sefaria.model import *
from mt_utilities import create_book_name_map, sefaria_book_names, export_data_to_csv, ALLOWED_TAGS, ALLOWED_ATTRS


def generate_html_report(txt, ref, unique_html_tags, unique_html_tag_dict_list):
    tags = re.findall(r"<(.*?)>", txt)
    for each_tag in tags:
        tag_name = re.findall(r"^(.*?)\s", each_tag)
        if tag_name:
            if tag_name[0] not in unique_html_tags:
                unique_html_tags[tag_name[0]] = 1

                # Save each first occurrence for report
                unique_html_tag_dict_list.append({
                    'tag': tag_name[0],
                    'example_ref': ref,
                    'example_text': txt
                })

            else:
                unique_html_tags[tag_name[0]] += 1


if __name__ == '__main__':
    unique_html_tags = {}
    unique_html_tag_dict_list = []
    cauldron_dir = './cauldron_data'
    for data in os.listdir(cauldron_dir):
        f = os.path.join(cauldron_dir, data)
        if os.path.isfile(f):
            with open(f, 'r') as file:
                with open(file.name, newline='') as csvfile:
                    r = csv.reader(csvfile, delimiter=',')
                    for halakha in r:
                        ref = halakha[0]
                        text = halakha[1]
                        generate_html_report(text, ref, unique_html_tags, unique_html_tag_dict_list)

    export_data_to_csv(unique_html_tag_dict_list, 'qa_reports/cauldron_html_report',
                       headers_list=['tag', 'example_ref', 'example_text'])
    print(unique_html_tags)