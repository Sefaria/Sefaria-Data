# -*- coding: utf-8 -*-

import django

django.setup()

import roman
import re
import csv
from sefaria.model import *
from sefaria.helper.schema import *


# From the list of links between the Mishnah and the Talmud,
# this function returns a list of Mishnah references
def get_mishnah_ref_array_from_talmud_links():
    ls = LinkSet({"type": "mishnah in talmud"})
    mishnah_ref_array = []
    for linked_mishnah in ls:
        mishnah_tref = linked_mishnah.refs[0] if "Mishnah" in linked_mishnah.refs[0] else linked_mishnah.refs[1]
        mishnah_ref = Ref(mishnah_tref)
        if mishnah_ref.is_range():
            split_refs = mishnah_ref.range_list()
            for each_ref in split_refs:
                mishnah_ref_array.append(each_ref)
        else:
            mishnah_ref_array.append(mishnah_ref)
    return mishnah_ref_array


# This function determines whether a given Mishnah ref
# has a 1:1 relationship with a passage of Talmud (thus indicating
# to us that it's the proper segment of Mishnah in the Talmud's translation)
#
# This function checks for multiple occurrences of a Mishnah ref
# in the list of Mishnahs linked to Talmud.
#
# Returns:
# TRUE - if the Mishnah ref/ranged ref is unique on the list (i.e. when you search for
#        Berakhot 1:2, you only see Berakhot 1:2 one time on the list, or
# FALSE - if the Mishnah ref / ranged ref is NOT unique of the list (i.e. Masechet XYZ 2:1-3,
#         but there's also a link to Masechet XYZ 2:1, 2:2 and 2:2-3.
def is_one_to_one(ref, mishnah_ref_array):
    split_refs = ref.range_list()
    res = True
    for each_ref in split_refs:
        tref = each_ref.normal()
        num_occurrences = mishnah_ref_array.count(tref)
        if num_occurrences >= 1:
            res = False
    return res


# Cleans the raw Talmud text of interfering HTML/metadata
# Leaves in the <super> tags for the Roman Numeral superscripts,
# and the <b> tags surrounding the first word of every Mishnah,
# in case that's useful for fine-tuning these results.
def clean_text(german_text):
    german_text = str(german_text)
    text_array = re.sub(r"<small>|<\/small>|,|\[|\]|\{|\}|\"|\'|\['', '", "", german_text)
    return text_array


# Strips the last newline character from text to enable CSV formatting
def strip_last_new_line(text):
    return text[:-1]


# Helper function for common Hebrew text grabbing sequence
def get_hebrew_mishnah(ref):
    tref = ref.normal()
    hebrew_mishnah = Ref(tref).text('he').text
    hebrew_mishnah = strip_last_new_line(hebrew_mishnah)
    return hebrew_mishnah


# Given a link between the mishnah and talmud, this function
# can conditionally return either the appropriate Mishnah ref
# or Talmud ref
def get_ref_from_link(mishnah_talmud_link):
    mishnah_ref, talmud_ref = mishnah_talmud_link.refs if "Mishnah" in mishnah_talmud_link.refs[0] else reversed(
        mishnah_talmud_link.refs)
    return Ref(mishnah_ref), Ref(talmud_ref)


# This function prints a summary of our Exploratory Data Analysis
def print_eda_summary(rn_good_count, rn_bad_count, count_single, num_not_one_to_one, total_refs):
    print("EDA (Exploratory Data Analysis) Summary:")
    print(
        f"{count_single} mishnahs are single refs. That's {round((count_single / total_refs) * 100)}% of our LinkSet")
    print(f"{total_refs - count_single} mishnahs are ranged refs and require Roman Numeral parsing work (if 1:1).")
    print(
        f"{rn_good_count} ranged ref mishnas have corresponding number of Roman Numerals. Of the ranged ref "
        f"mishnahs, this is {round((rn_good_count / (total_refs - count_single)) * 100)}%")
    print(
        f"{rn_bad_count} ranged ref mishnas don't have corresponding number of Roman Numerals (maybe duplicates, "
        f"omissions etc)")
    print(f"{num_not_one_to_one} of the ranged ref mishnas are not 1:1")


# This is the main function which does the bulk of the scraping work.
# It returns a dictionary with the Mishnahs and corresponding helpful metadata
# If you set the param generate_eda_summary to True, it also
# outputs helpful exploratory data analysis statistics which we used during our parsing planning.
def scrape_german_mishnah_text(generate_eda_summary=False):
    mishnah_ref_array = get_mishnah_ref_array_from_talmud_links()

    mishnah_txt_list = []

    ls = LinkSet({"type": "mishnah in talmud"})

    # EDA Summary Set Up
    rn_good_count = 0
    rn_bad_count = 0
    count_single = 0
    num_not_one_to_one = 0
    total_refs = len(ls)

    for mishnah_talmud_link in ls:

        # default assumptions
        one_to_one = True
        flagged = False
        flag_msg = ""
        mishnah_ref, talmud_ref = get_ref_from_link(mishnah_talmud_link)

        german_text = talmud_ref.text('en', vtitle='Talmud Bavli. German trans. by Lazarus Goldschmidt, 1929 [de]')
        german_text = german_text.text
        german_text = clean_text(german_text)

        # Find all Roman Numerals in the German text, and save to an array
        all_roman_numerals = re.findall(r"<sup>([ixv]+).*?<\/sup>", german_text)

        if mishnah_ref.is_range():

            # add a one-to-one check
            one_to_one = is_one_to_one(mishnah_ref, mishnah_ref_array)
            num_mishnahs = len(mishnah_ref.range_list())

            # Flag messages
            if not one_to_one:
                num_not_one_to_one += 1
                flagged = True
                flag_msg += "Not one to one"

            if num_mishnahs != len(all_roman_numerals):
                rn_bad_count += 1
                flagged = True
                if len(flag_msg) > 1:
                    flag_msg += ", "  # append if both
                flag_msg += "Roman numeral mismatch"

            else:
                rn_good_count += 1

                # If a ranged ref that's one-to-one, with a correct Roman Numeral set,
                # we can easily further break down the ranged ref into its components.
                if one_to_one:

                    individual_mishnahs = re.split(r"<sup>[ixv].*?<\/sup>", german_text)

                    split_refs = mishnah_ref.range_list()
                    counter = 1  # since '' is at 0

                    for each_ref in split_refs:
                        hebrew_mishnah = get_hebrew_mishnah(each_ref)
                        mishnah_tref = each_ref.normal()
                        mishnah_txt_list.append({'tref': mishnah_tref,
                                                 'german_text': individual_mishnahs[counter],
                                                 'hebrew_text': hebrew_mishnah,
                                                 "is_one_to_one": one_to_one,
                                                 "flagged_for_manual": flagged,
                                                 "flag_msg": flag_msg,
                                                 "list_rn": all_roman_numerals})
                        counter += 1

                    continue

            # If the Mishnah is a ranged ref, and has been flagged
            # break it up without any German text passed the first
            # Mishnah in the ref for a clear visual indicator to the
            # team manually parsing.
            split_refs = mishnah_ref.range_list()
            first_ref = True
            for each_ref in split_refs:
                hebrew_mishnah = get_hebrew_mishnah(each_ref)
                mishnah_tref = each_ref.normal()

                if not first_ref:
                    german_text = ""

                first_ref = False

                mishnah_txt_list.append({'tref': mishnah_tref,
                                         'german_text': german_text,
                                         'hebrew_text': hebrew_mishnah,
                                         "is_one_to_one": one_to_one,
                                         "flagged_for_manual": flagged,
                                         "flag_msg": flag_msg,
                                         "list_rn": all_roman_numerals})

            continue

        else:
            count_single += 1

        if not flagged:
            hebrew_mishnah = mishnah_ref.text('he').text
            hebrew_mishnah = strip_last_new_line(hebrew_mishnah)

        # Base case (one to one, not a ranged ref)
        # Saves the Mishnah with the corresponding Hebrew text
        mishnah_txt_list.append({'tref': mishnah_ref.normal(),
                                 'german_text': german_text,
                                 'hebrew_text': hebrew_mishnah,
                                 "is_one_to_one": one_to_one,
                                 "flagged_for_manual": flagged,
                                 "flag_msg": flag_msg,
                                 "list_rn": all_roman_numerals})

    if generate_eda_summary:
        print_eda_summary(rn_good_count,
                          rn_bad_count,
                          count_single,
                          num_not_one_to_one,
                          total_refs)

    return mishnah_txt_list


# This function generates the CSV of the Mishnayot
def generate_csv_german_mishna():
    mishnah_list = scrape_german_mishnah_text()

    # pipe delimiter instead of comma, since comma in text
    headers = ['tref', 'german_text', 'hebrew_text', 'is_one_to_one', 'flagged_for_manual', 'flag_msg',
               'list_rn']

    with open(f'Goldschmidt German Mishnah/german_mishnah_data.csv', 'w') as file:
        mishnah_list.sort(key=lambda x: Ref(x["tref"]).order_id())
        c = csv.DictWriter(file, delimiter='|', fieldnames=headers)
        c.writeheader()
        c.writerows(mishnah_list)

    print("File writing complete")


if __name__ == "__main__":
    generate_csv_german_mishna()
