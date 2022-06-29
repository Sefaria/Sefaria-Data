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
    with open('german_mishnah_data_original.csv', newline='') as csvfile:
        german_mishnah_csv = csv.DictReader(csvfile)
        for row in german_mishnah_csv:
            cleaned_text = re.sub(r"<sup>([xvilcdm]*)<\/sup>|<sup>([xvilcdm]*,\d)<\/sup>", "", row['de_text'])
            cur_row_dict = {"mishnah_tref": row['mishnah_tref'], "de_text": cleaned_text}
            dict_list.append(cur_row_dict)
    return dict_list


def renumber_footnotes_by_chapter(list_of_rows):
    chapter = 1
    count = 1
    renumbered_list = []
    for row in list_of_rows:
        cur_chapter = Ref(row['mishnah_tref']).sections[0]
        de_text = row['de_text']
        if chapter != cur_chapter:
            # Reset chapter
            chapter = cur_chapter
            # Reset the count
            count = 1

        # Todo - comment this (from @shanee - add space if no punctuation (also just stam fix!!)
        matches = re.finditer(r"<sup>(\d*)<\/sup><i class=\"footnote\">", row['de_text'])
        fixed_footnote_text = ''
        is_first_match = True
        old_idx = 0
        for match in matches:
            start_idx = match.start()
            end_idx = match.end()
            match_str = de_text[start_idx:end_idx]
            fixed_footnote = re.sub(r"\d+", str(count), match_str)

            if is_first_match:
                fixed_footnote_text += de_text[:start_idx]
            else:
                fixed_footnote_text += de_text[old_idx:start_idx]

            fixed_footnote_text += fixed_footnote
            count += 1
            is_first_match = False
            old_idx = end_idx

        if len(fixed_footnote_text) > 1:
            renumbered_list.append({'mishnah_tref': row['mishnah_tref'], 'de_text': fixed_footnote_text})
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
