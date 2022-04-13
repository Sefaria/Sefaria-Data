# -*- coding: utf-8 -*-

import django

django.setup()

import roman
import re
import csv
from sefaria.model import *

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


# Helper function for 1:1 check
def checking_one_to_one(ref, mishnah_ref_array):
    num_occurrences = mishnah_ref_array.count(ref)
    if num_occurrences > 1:
        print(num_occurrences)
        return False
    return True


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
    result = True
    if ref.is_range():
        split_refs = ref.range_list()
        for each_ref in split_refs:
            result = checking_one_to_one(each_ref, mishnah_ref_array)
    else: # if single ref
        result = checking_one_to_one(ref, mishnah_ref_array)
    return result


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


def get_german_text(talmud_ref):
    german_text = talmud_ref.text('en', vtitle='Talmud Bavli. German trans. by Lazarus Goldschmidt, 1929 [de]')
    german_text = german_text.text
    german_text = clean_text(german_text)
    return german_text


# Given a link between the mishnah and talmud, this function
# can conditionally return either the appropriate Mishnah ref
# or Talmud ref
def get_ref_from_link(mishnah_talmud_link):
    mishnah_ref, talmud_ref = mishnah_talmud_link.refs if "Mishnah" in mishnah_talmud_link.refs[0] else reversed(
        mishnah_talmud_link.refs)
    return Ref(mishnah_ref), Ref(talmud_ref)


# Return the dict item
def get_mishnah_data(ref, german_text, one_to_one, flagged, flag_msg, all_roman_numerals):
    hebrew_mishnah = get_hebrew_mishnah(ref)
    mishnah_tref = ref.normal()
    return {'tref': mishnah_tref,
            'german_text': german_text,
            'hebrew_text': hebrew_mishnah,
            "is_one_to_one": one_to_one,
            "flagged_for_manual": flagged,
            "flag_msg": flag_msg,
            "list_rn": all_roman_numerals}


# This is the main function which does the bulk of the scraping work.
# It returns a dictionary with the Mishnahs and corresponding helpful metadata
# If you set the param generate_eda_summary to True, it also
# outputs helpful exploratory data analysis statistics which we used during our parsing planning.
def scrape_german_mishnah_text():
    mishnah_ref_array = get_mishnah_ref_array_from_talmud_links()

    mishnah_txt_list = []

    ls = LinkSet({"type": "mishnah in talmud"})

    for mishnah_talmud_link in ls:

        # default assumptions
        flagged = False
        flag_msg = ""

        mishnah_ref, talmud_ref = get_ref_from_link(mishnah_talmud_link)
        german_text = get_german_text(talmud_ref)

        # Find all Roman Numerals in the German text, and save to an array
        all_roman_numerals = re.findall(r"<sup>([ixv]+).*?<\/sup>", german_text)

        # add a one-to-one check
        one_to_one = is_one_to_one(mishnah_ref, mishnah_ref_array)

        # Flag messages
        if not one_to_one:
            flagged = True
            flag_msg = "Not one to one"

        if mishnah_ref.is_range():

            # Mishmatch between the number of Mishnahs and the
            # number of Roman Numerals
            if len(mishnah_ref.range_list()) != len(all_roman_numerals) or not one_to_one:
                flagged = True
                flag_msg += "Roman numeral mismatch" if len(flag_msg) < 1 else ", Roman numeral mismatch"

                # If the Mishnah is a ranged ref, and has been flagged
                # break it up without any German text passed the first
                # Mishnah in the ref for a clear visual indicator to the
                # team manually parsing.
                split_refs = mishnah_ref.range_list()
                first_ref = True
                for each_ref in split_refs:
                    german_text = "" if not first_ref else german_text
                    first_ref = False
                    mishnah_txt_list.append(
                        get_mishnah_data(each_ref, german_text, one_to_one, flagged, flag_msg, all_roman_numerals))


            # If a ranged ref that's one-to-one, with a correct Roman Numeral set,
            # we can easily further break down the ranged ref into its components.
            else:
                individual_mishnahs = re.split(r"<sup>[ixv].*?<\/sup>", german_text)
                split_refs = mishnah_ref.range_list()
                counter = 1  # since '' is at 0

                for each_ref in split_refs:
                    german_text = individual_mishnahs[counter]
                    mishnah_txt_list.append(
                        get_mishnah_data(each_ref, german_text, one_to_one, flagged, flag_msg, all_roman_numerals))
                    counter += 1

        else: #TODO - how do we handle not 1:1 single refs?
            # Base case (not a ranged ref - may or may not be 1:1)
            # Saves the Mishnah with the corresponding Hebrew text
            mishnah_txt_list.append(
                get_mishnah_data(mishnah_ref, german_text, one_to_one, flagged, flag_msg, all_roman_numerals))

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
