# -*- coding: utf-8 -*-

import django

django.setup()

import roman
import statistics
import re
import csv
from sefaria.model import *


def remove_roman_numerals():
    with open('german_mishnah_data.csv', newline='') as csvfile:
        german_mishnah_csv = csv.DictReader(csvfile)
        for row in german_mishnah_csv:
            # Todo - fix where it's being saved based on implementation (i.e.
            # to the CSV, in the ingest script etc?)
            row['de_text'] = re.sub(r"<sup>([xvilcdm]*)<\/sup>", "", row['de_text'])


def identify_chapter(tref):
    chapter = re.findall(r".* (\d*):", tref)[0]
    return int(chapter)


def renumber_footnotes_by_chapter():
    with open('german_mishnah_data.csv', newline='') as csvfile:
        german_mishnah_csv = csv.DictReader(csvfile)
        chapter = 1
        count = 1
        for row in german_mishnah_csv:
            cur_chapter = identify_chapter(row['mishnah_tref'])
            if chapter != cur_chapter:
                # Reset chapter
                chapter = cur_chapter
                # Reset the count
                count = 1

            # Todo - again based on what Noah says decide where to save
            if 'footnote' in row['de_text']:
                row['de_text'] = re.sub(r"<sup>(\d*)<\/sup><i class=""footnote"">", str(count), row['de_text'])
                count += 1


renumber_footnotes_by_chapter()