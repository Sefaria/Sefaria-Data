# -*- coding: utf-8 -*-
"""
todo:
- cvs to 2 cols

key:
new mishnah: p class: u"_-המשנה-בירוק-שורה-1"
lines of mishnah: p class: u"_-המשנה-בירוק"
running text: p class: u"_טקסט-רץ"
mishnah in commentary: span class: u"_-פירוש-בירוק"
:: after mishnah: span class: u"_-"
dashes in commentary: span class: u"CharOverride-25"
green headlines: p class u"_-כותרת-ירוקה"
perek/amud: p class: u"_-מספר-עמוד ParaOverride-9"
page number: p class: u"_-מספר-עמוד"
pic info: p class: u"__כיתוב-לתמונה"
          p class: u"_-שם-התמונה"
"""
import re
import csv
import os
import io
import sys
import pdb
import codecs
from bs4 import BeautifulSoup
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from data_utilities import util
from sources.local_settings import *
from sources import functions
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedArray
from sefaria.utils.hebrew import decode_hebrew_numeral as gematria

def parse(html_page, csv_page):

    ja = []
    chapters, mishnayot, segments = {}, {}, []
    cur_chap, new_chap, cur_mishna, new_mishna = None, None, None, None

    infile = io.open(html_page, 'r')
    soup = BeautifulSoup(infile, 'html5lib')
    infile.close()

    infile = io.open(csv_page, 'r')
    reader = csv.reader(infile)
    infile.close()
    dist_dict = dict((rows[0], rows[1] + ':' + rows[2] + '-' + rows[3]) for rows in reader)

    return ja


def build_index():

    schema = JaggedArrayNode()
    schema.add_primary_titles(u'', u'')
    schema.add_structure(["Chapter", "Verse", "Comment"])
    schema.validate()

    index = {
        "title": "",
        "categories": [],
        "schema": schema.serialize()
    }

    return index

def upload_text(parsed_text):

    version = {
            "versionTitle": "",
            "versionSource": "",
            "language": 'he',
            "text": parsed_text
        }
    functions.post_text("", version, index_count='on')

def build_links(parsed_text):
    pass


if __name__ == '__main__':
    jagged_array = parse(html_path, csv_path)
    util.ja_to_xml(jagged_array, ['Chapter', 'Verse', 'Commentary'])
    #functions.post_index(build_index())
    #upload_text(jagged_array)
    #functions.post_link(build_links(jagged_array))
