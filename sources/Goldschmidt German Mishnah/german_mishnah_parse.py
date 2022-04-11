# -*- coding: utf-8 -*-

import django

django.setup()

import roman
import re
from sefaria.model import *
from sefaria.helper.schema import *


# From the list of links between the Mishnah and the Talmud,
# this function returns a list of Mishnah references
def get_mishnah_ref_array_from_talmud_links():
    ls = LinkSet({"type": "mishnah in talmud"})
    mishnah_ref_array = []
    for linked_mishnah in ls:
        refs = linked_mishnah.refs

        if "Mishnah" in refs[0]:
            mishnah_ref = refs[0]
        else:
            mishnah_ref = refs[1]

        mishnah_ref_array.append(mishnah_ref)
    return mishnah_ref_array


# This function determines whether or not a given Mishnah ref
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
    split_refs = Ref(ref).range_list()
    res = True
    for each_ref in split_refs:
        mishnah_title = str(each_ref)
        num_occurrences = mishnah_ref_array.count(mishnah_title)
        if num_occurrences >= 1:
            res = False
    return res


# Cleans the raw Talmud text of interfering HTML/metadata
# Leaves in the <super> tags for the Roman Numeral superscripts,
# and the <b> tags surrounding the first word of every Mishnah,
# in case that's useful for fine tuning these results.
def clean_text(text):
    text_array = TextChunk._strip_itags(text)
    text_array = re.sub(r"<i>|<\/i>|<small>|<\/small>|,|\[|\]|\{|\}|\"|\'|\['', '", "",
                        text_array)  # TODO - clean up and streamline this regex
    return text_array


# Strips the last newline character from text to enable CSV formatting
def strip_last_new_line(text):
    return text[:-1]


# This is the main function which does the bulk of the scraping work.
# It returns a dictionary with the Mishnahs and corresponding helpful metadata
# If you set the param generate_eda_summary to True, it also
# outputs helpful exploratory data analysis statistics which we used during our parsing planning.
def scrape_german_mishnah_text(generate_eda_summary=False):
    mishnah_ref_array = get_mishnah_ref_array_from_talmud_links()

    mishnah_txt_dict = {}

    ls = LinkSet({"type": "mishnah in talmud"})
    rn_good_count = 0
    rn_bad_count = 0
    count_single = 0
    num_not_one_to_one = 0
    total_refs = len(ls)

    for link in ls:

        hebrew_mishnah = ""  # will remain blank if manual parsing is needed

        # default assumptions
        one_to_one = True
        flagged = False
        flag_msg = ""

        refs = link.refs
        num_mishnahs = 1

        if "Mishnah" in refs[0]:
            mishnah_ref = refs[0]
            talmud_ref = refs[1]
        else:
            mishnah_ref = refs[1]
            talmud_ref = refs[0]

        german_text = Ref(talmud_ref).text('en', vtitle='Talmud Bavli. German trans. by Lazarus Goldschmidt, '
                                                        '1929 [de]').text

        german_text = clean_text(german_text)

        # Find RN
        all_roman_numerals = re.findall(r"<sup>([ixv]+).*?<\/sup>", german_text)

        is_multiple_mishnahs = re.search(r"Mishnah [a-zA-Z\s]*\s\d.*?:\d.*?-", mishnah_ref)

        if is_multiple_mishnahs:

            # add a one-to-one check
            one_to_one = is_one_to_one(mishnah_ref, mishnah_ref_array)
            num_mishnahs = len(Ref(mishnah_ref).range_list())

            if not one_to_one:
                num_not_one_to_one += 1
                flagged = True
                flag_msg += "Not one to one"

            if num_mishnahs != len(all_roman_numerals):
                rn_bad_count += 1
                flagged = True
                if len(flag_msg) > 1:
                    flag_msg += ", "  # append if botb
                flag_msg += "Roman numeral mismatch"

            else:
                rn_good_count += 1

                # If a ranged ref that's one-to-one, with a correct Roman Numeral set,
                # we can easily further break down the ranged ref into its components.
                if one_to_one:

                    individual_mishnahs = re.split(r"<sup>[ixv].*?<\/sup>", german_text)

                    split_refs = Ref(mishnah_ref).range_list()
                    counter = 1  # since '' is at 0

                    for each_ref in split_refs:
                        mishnah_title = str(each_ref)
                        hebrew_mishnah = Ref(mishnah_title).text('he').text
                        hebrew_mishnah = strip_last_new_line(hebrew_mishnah)
                        mishnah_txt_dict[mishnah_title] = {'ref': mishnah_title,
                                                           'german_text': individual_mishnahs[counter],
                                                           'hebrew_text': hebrew_mishnah,
                                                           "is_one_to_one": one_to_one,
                                                           "flagged_for_manual": flagged,
                                                           "flag_msg": flag_msg,
                                                           "total_mishnahs": num_mishnahs,
                                                           "total_roman_numerals": len(all_roman_numerals),
                                                           "list_rn": all_roman_numerals}
                        counter += 1

                    continue

        else:
            count_single += 1

        if not flagged:
            hebrew_mishnah = Ref(mishnah_ref).text('he').text
            hebrew_mishnah = strip_last_new_line(hebrew_mishnah)

        mishnah_txt_dict[mishnah_ref] = {'ref': mishnah_ref,
                                         'german_text': german_text,
                                         'hebrew_text': hebrew_mishnah,
                                         "is_one_to_one": one_to_one,
                                         "flagged_for_manual": flagged,
                                         "flag_msg": flag_msg,
                                         "total_mishnahs": num_mishnahs,
                                         "total_roman_numerals": len(all_roman_numerals),
                                         "list_rn": all_roman_numerals}

    if generate_eda_summary:
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

    return mishnah_txt_dict


def generate_csv_german_mishna(print_csv=False):
    mishnah_dict = scrape_german_mishnah_text()

    # pipe delimiter instead of comma, since comma in text
    csv_string = 'mishnah_ref|german_text|hebrew_text|is_one_to_one|flagged_for_manual|flag_msg|total_mishnahs|total_roman_numerals|list_rn\n'

    for mishnah in mishnah_dict:
        cur_mishnah = mishnah_dict[mishnah]
        csv_string += f"{mishnah}|{cur_mishnah['german_text']}|{cur_mishnah['hebrew_text']}|{cur_mishnah['is_one_to_one']}|{cur_mishnah['flagged_for_manual']}|{cur_mishnah['flag_msg']}|{cur_mishnah['total_mishnahs']}|{cur_mishnah['total_roman_numerals']}|{cur_mishnah['list_rn']}\n"

    if print_csv:
        print(csv_string)

    with open(f'german_mishnah_data.csv', 'w') as file:
        for line in csv_string:
            file.write(line)

    print("File writing complete")


generate_csv_german_mishna(print_csv=False)
# scrape_german_mishnah_text(generate_eda_summary=True)

