# -*- coding: utf-8 -*-

import django

django.setup()

import roman
import statistics
import re
import csv
from sefaria.model import *


def remove_roman_numerals():
    dict_list = []
    with open('german_mishnah_data.csv', newline='') as csvfile:
        german_mishnah_csv = csv.DictReader(csvfile)
        for row in german_mishnah_csv:
            cleaned_text = re.sub(r"<sup>([xvilcdm]*)<\/sup>", "", row['de_text'])
            cur_row_dict = {"mishnah_tref": row['mishnah_tref'], "de_text": cleaned_text}
            dict_list.append(cur_row_dict)
    return dict_list



def identify_chapter(tref):
    chapter = re.findall(r".* (\d*):", tref)[0]
    return int(chapter)


def renumber_footnotes_by_chapter(list_of_rows):
        chapter = 1
        count = 1
        renumbered_list = []
        for row in list_of_rows:
            renumbered_text = ""
            cur_chapter = identify_chapter(row['mishnah_tref'])
            if chapter != cur_chapter:
                # Reset chapter
                chapter = cur_chapter
                # Reset the count
                count = 1

            if 'footnote' in row['de_text']:
                renumbered_text = re.sub(r"<sup>(\d*)<\/sup><i class=""footnote"">", str(count), row['de_text'])
                count += 1

            if len(renumbered_text) > 1:
                renumbered_list.append({'mishnah_tref': row['mishnah_tref'], 'de_text': renumbered_text})
            else:
                renumbered_list.append(row)
        return renumbered_list


# This function generates the CSV of the Mishnayot
def generate_csv(mishnah_list):
    headers = ['mishnah_tref',
               'de_text']
    with open(f'german_mishnah_data_cleaned.csv', 'w+') as file:
        mishnah_list.sort(key=lambda x: Ref(x["mishnah_tref"]).order_id())
        c = csv.DictWriter(file, fieldnames=headers)
        c.writeheader()
        c.writerows(mishnah_list)

    print("File writing complete")


# Updates the CSV to renumber the footnotes and delete the roman numerals
def run():
    mishnah_list = remove_roman_numerals()
    mishnah_list = renumber_footnotes_by_chapter(mishnah_list)
    generate_csv(mishnah_list)


if __name__ == "__main__":
    run()