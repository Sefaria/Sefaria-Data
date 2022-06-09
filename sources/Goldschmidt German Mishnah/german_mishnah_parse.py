# -*- coding: utf-8 -*-

import django

django.setup()

import roman
import statistics
import re
import csv
from sefaria.model import *


#### UTILITY FUNCTIONS ####

# Helper function for 1:1 check
def checking_one_to_one(ref, mishnah_ref_array):
    num_occurrences = mishnah_ref_array.count(ref)
    if num_occurrences > 1:
        return False
    return True


# Cleans the raw Talmud text of interfering HTML/metadata
# Leaves in the <super> tags for the Roman Numeral superscripts,
# and the <b> tags surrounding the first word of every Mishnah,
# in case that's useful for fine-tuning these results.
def clean_text(german_text):
    german_text = str(german_text)
    text_array = re.sub(r"\[|\]|\{|\}", "", german_text)
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


# Helper function which, given a tref, returns the text
def get_german_text(talmud_ref):
    german_text = talmud_ref.text('en', vtitle='Talmud Bavli. German trans. by Lazarus Goldschmidt, 1929 [de]')
    german_text = german_text.text
    german_text = clean_text(german_text)
    return german_text


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
    else:  # if single ref
        result = checking_one_to_one(ref, mishnah_ref_array)
    return result


# This function creates a list of mishnah trefs, and extracts any masechtot
# that are not also found in the Bavli (i.e. Pirkei Avot), since this project
# is focused only on those masechtot which may have a translation in the
# Bavli already.
def create_list_of_mishnah_trefs():
    mishnah_indices = library.get_indexes_in_category("Mishnah", full_records=True)
    full_tref_list = []
    for index in mishnah_indices:
        mishnah_refs = index.all_segment_refs()
        for mishnah in mishnah_refs:
            full_tref_list.append(mishnah.normal())

    # Clean out non-Bavli references
    talmud_indices = library.get_indexes_in_category("Bavli")
    i = 0
    while i < len(full_tref_list):
        cur_ref = full_tref_list[i]
        masechet = re.findall(r"[A-Za-z ] ([A-Za-z ].*?) \d", cur_ref)
        if masechet and masechet[0] not in talmud_indices:
            full_tref_list.remove(full_tref_list[i])
            continue
        i += 1

    return full_tref_list


# This is a helper function which calculates specific mishnah statistics
# regarding the length of the texts, and the ratio between the German and the Hebrew
# to help indicate errors in the parsing.
# The method is as follows:
#
# For each mishnah
# - strip german html and footnotes
# - calculate word len for each
# - create a len ratio list
# - find the mean of that list as the stdev mean
# - return mean and stdev
def mishnah_statistics(mishnah_list):
    ratio_list = []
    missing_mishnahs = 0
    ratio_aggregate = 0

    for each_mishnah in mishnah_list:

        german_text = TextChunk._strip_itags(each_mishnah['german_text'])
        german_text = re.sub(r'<.*?>', '', german_text)
        hebrew_text = each_mishnah['hebrew_text']

        if len(german_text) > 10:
            ratio_he_to_de = len(hebrew_text) / len(german_text)
            ratio_aggregate += ratio_he_to_de
            ratio_list.append(ratio_he_to_de)

    # done manually to account for missing mishnahs
    mean_of_ratios = ratio_aggregate / (len(mishnah_list) - missing_mishnahs)
    stdev = statistics.stdev(ratio_list)
    return mean_of_ratios, stdev


# Return the dict item representing each row of the CSV
def get_mishnah_data(ref, talmud_tref, german_text, one_to_one, flagged, flag_msg, all_roman_numerals):
    hebrew_mishnah = get_hebrew_mishnah(ref)
    mishnah_tref = ref.normal()
    return {'mishnah_tref': mishnah_tref,
            'talmud_tref': talmud_tref,
            'german_text': german_text,
            'hebrew_text': hebrew_mishnah,
            "is_one_to_one": one_to_one,
            "flagged_for_manual": flagged,
            "flag_msg": flag_msg,
            "list_rn": all_roman_numerals,
            "length_flag": ''}


# This function generates the CSV of the Mishnayot
def generate_csv_german_mishnah(mishnah_list):
    # pipe delimiter instead of comma, since comma in text
    headers = ['mishnah_tref',
               'talmud_tref',
               'german_text',
               'hebrew_text',
               'is_one_to_one',
               'flagged_for_manual',
               'flag_msg',
               'list_rn',
               'length_flag']

    with open(f'Goldschmidt German Mishnah/german_mishnah_parsing_data.csv', 'w') as file:
        mishnah_list.sort(key=lambda x: Ref(x["mishnah_tref"]).order_id())
        c = csv.DictWriter(file, delimiter='|', fieldnames=headers)
        c.writeheader()
        c.writerows(mishnah_list)

    print("File writing complete")


### SCRAPING FUNCTIONS ####

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


# Given a link between the mishnah and talmud, this function
# can conditionally return either the appropriate Mishnah ref
# or Talmud ref
def get_ref_from_link(mishnah_talmud_link):
    mishnah_ref, talmud_ref = mishnah_talmud_link.refs if "Mishnah" in mishnah_talmud_link.refs[0] else reversed(
        mishnah_talmud_link.refs)
    return Ref(mishnah_ref), Ref(talmud_ref)


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
                    german_text = german_text if first_ref else ""
                    first_ref = False
                    mishnah_txt_list.append(
                        get_mishnah_data(each_ref, talmud_ref.normal(), german_text, one_to_one, flagged, flag_msg, all_roman_numerals))

            # If a ranged ref that's one-to-one, with a correct Roman Numeral set,
            # we can easily further break down the ranged ref into its components.
            else:
                individual_mishnahs = re.split(r"<sup>[ixv].*?<\/sup>", german_text)
                split_refs = mishnah_ref.range_list()
                counter = 1  # since '' is at 0
                rn_count = 0

                for each_ref in split_refs:
                    german_text = individual_mishnahs[counter]
                    german_text = f"<sup>{all_roman_numerals[rn_count]}</sup>{german_text}"
                    rn_count += 1
                    mishnah_txt_list.append(
                        get_mishnah_data(each_ref, talmud_ref, german_text, one_to_one, flagged, flag_msg, all_roman_numerals))
                    counter += 1

        else:
            # Base case (not a ranged ref - may or may not be 1:1)
            # Saves the Mishnah with the corresponding Hebrew text
            mishnah_txt_list.append(
                get_mishnah_data(mishnah_ref, talmud_ref, german_text, one_to_one, flagged, flag_msg, all_roman_numerals))

    return mishnah_txt_list


#### FUNCTIONS FOR POST-PROCESSING DATA ###

# This function takes sections of the same mishnah, and condenses
# them based on their roman numerals
def merge_segments_of_mishnah(mishnah_list):
    # If this tref matches the previous one
    # if the roman numerals are sequential (check for multiple RN?)
    # append this text to the previous one
    # delete this entry
    i = 1
    while i < len(mishnah_list):  # dynamic list size

        prev_mishnah = mishnah_list[i - 1]
        cur_mishnah = mishnah_list[i]

        # Two of the same
        if cur_mishnah['mishnah_tref'] == prev_mishnah['mishnah_tref']:
            # Check roman numerals
            prev_num = re.findall(r"<sup>[ixv].*?(\d)<\/sup>", prev_mishnah['german_text'])
            cur_num = re.findall(r"<sup>[ixv].*?(\d)<\/sup>", cur_mishnah['german_text'])
            prev_num = int(prev_num[0]) if len(prev_num) == 1 else None
            cur_num = int(cur_num[0]) if len(cur_num) == 1 else None
            if cur_num and prev_num and cur_num - prev_num == 1:
                prev_mishnah['german_text'] += cur_mishnah['german_text']
                prev_mishnah['flag_msg'] += ", been merged."
                prev_mishnah['flagged_for_manual'] = False  # no longer needs manual parsing
                mishnah_list.remove(cur_mishnah)
        i += 1
    return mishnah_list


def condense_blanks(mishnah_list):
    # Condense later blanks
    # Flag duplicates where one is blank
    # if the duplicate non-empty starts with a rn-2, look to see if rn-1 is in previous
    # If so, extract it and append it to the non-empty one, and delete the blank
    for i in range(0, len(mishnah_list)):
        cur_mishnah = mishnah_list[i]

        # set neighbors
        next_mishnah = mishnah_list[i + 1] if i < len(mishnah_list) - 1 else None
        prev_mishnah = mishnah_list[i - 1] if i >= 1 else None

        if cur_mishnah['german_text'] == '' and prev_mishnah and next_mishnah:
            # If this blank, has a duplicated non-blank for the same tref
            if cur_mishnah['mishnah_tref'] == next_mishnah['mishnah_tref'] and next_mishnah['german_text'] != '':
                # check that the next mishnah's first rn is not 1

                # Scrape non-empty neighbors for all their roman numerals
                next_mishnah_rn_num = re.findall(r"<sup>[ixv].*?(\d)<\/sup>", next_mishnah['german_text'])
                prev_mishnah_rn_num = re.findall(r"<sup>[ixv].*?(\d)<\/sup>", prev_mishnah['german_text'])

                if '1' in prev_mishnah_rn_num:
                    cur_mishnah_number = re.findall(r".* \d.*:(\d.*)", cur_mishnah['mishnah_tref'])
                    cur_mishnah_number = int(cur_mishnah_number[0])
                    cur_mishnah_rn = roman.toRoman(cur_mishnah_number).lower()
                    pattern = re.compile(f"(<sup>{cur_mishnah_rn}\d<\/sup>.*)$")

                    # Capture text
                    misplaced_text = re.findall(pattern, prev_mishnah['german_text'])

                    # Append to new
                    if len(misplaced_text) >= 1:
                        cur_mishnah['german_text'] = misplaced_text[0] + next_mishnah['german_text']
                    else:
                        cur_mishnah['flagged_for_manual'] = True

                    if next_mishnah_rn_num and next_mishnah_rn_num[0] != '2':
                        cur_mishnah['flagged_for_manual'] = True
                        cur_mishnah["flag_msg"] = 'Condensed, but non-sequential RN-numeric tags'

                    # Remove from previous
                    index_next_mishnah = prev_mishnah['german_text'].find(f"<sup>{cur_mishnah_rn}")
                    prev_mishnah['german_text'] = prev_mishnah['german_text'][:index_next_mishnah]

                    # Flag next_mishnah for removal
                    next_mishnah['flag_msg'] = 'REMOVE'

    new_mishnah_list = list(filter(lambda mishnah: mishnah['flag_msg'] != 'REMOVE', mishnah_list))

    return new_mishnah_list


def extract_joined_mishnahs(mishnah_list):
    count = 0
    for i in range(0, len(mishnah_list) - 1):
        cur_mishnah = mishnah_list[i]
        next_mishnah = mishnah_list[i + 1]

        # If current mishnah is not blank, but the next one is... (expand for more than 1 blank later)
        if cur_mishnah['german_text'] != '' and next_mishnah['german_text'] == '':
            next_mishnah_number = re.findall(r".* \d.*:(\d.*)", next_mishnah['mishnah_tref'])
            next_mishnah_number = int(next_mishnah_number[0])
            next_mishnah_rn = roman.toRoman(next_mishnah_number).lower()

            pattern = re.compile(f"(<sup>{next_mishnah_rn}<\/sup>.*)$")

            # Capture text
            misplaced_text = re.findall(pattern, cur_mishnah['german_text'])

            # Append to new
            next_mishnah['german_text'] = misplaced_text[0] if misplaced_text else ''

            # Current mishnah no longer needs parsing if one-to-one
            if 'Not one to one' not in cur_mishnah['flag_msg']:
                cur_mishnah['flagged_for_manual'] = False

            # If the next mishnah was embedded, reset the error flags for the mishnahs
            if next_mishnah['german_text'] != "":
                cur_mishnah["flag_msg"] = f"Extracted {next_mishnah['mishnah_tref']} from this mishnah"
                next_mishnah['flagged_for_manual'] = False
                next_mishnah[
                    'flag_msg'] = f"This Mishnah text was taken from {cur_mishnah['mishnah_tref']} where it was embedded"

                # Remove extra text from current mishnah
                index_extra_text = cur_mishnah['german_text'].find(f"<sup>{next_mishnah_rn}")
                cur_mishnah['german_text'] = cur_mishnah['german_text'][:index_extra_text]
                count += 1
    return mishnah_list


def catch_edge_cases(mishnah_list):
    i = 0
    while i < len(mishnah_list):
        mishnah = mishnah_list[i]
        nxt_mishnah = mishnah_list[i + 1] if i < (len(mishnah_list) - 1) else None
        # If just a roman numeral
        if len(mishnah['german_text']) < 20:
            mishnah['flagged_for_manual'] = True
            mishnah['flag_msg'] = 'Suspected insufficiency in text'

        # If duplicated mishnahs and one is NOT one-to-one and the other is, delete the NOT one-to-one one.
        if nxt_mishnah and mishnah['mishnah_tref'] == nxt_mishnah['mishnah_tref']:
            if mishnah['is_one_to_one'] == False and nxt_mishnah['is_one_to_one'] == True:
                mishnah_list.remove(mishnah)
            elif nxt_mishnah['is_one_to_one'] == False and mishnah['is_one_to_one'] == True:
                mishnah_list.remove(nxt_mishnah)
        i += 1

    return mishnah_list


# Validate that all Mishnahs are in this list
def validate_mishna(mishnah_list):
    full_tref_list = create_list_of_mishnah_trefs()
    mishnah_list_trefs = [mishnah['mishnah_tref'] for mishnah in mishnah_list]
    not_included = set(full_tref_list) - set(mishnah_list_trefs)
    return not_included


# Create empty slots for Mishnahs that are missing (order doesn't matter
# since sorted upon CSV creation)
def add_empty(mishnah_list):
    not_included = validate_mishna(mishnah_list)

    for each_ref in not_included:
        # Query the Talmud Link
        ls = LinkSet({'refs': each_ref, 'type': 'mishnah in talmud'})
        talmud_tref = None
        for link in ls:
            talmud_tref = link.refs[0] if "Mishnah" not in link.refs[0] else link.refs[1]
            talmud_tref = talmud_tref.normal()
        if talmud_tref:
            mishnah_data = get_mishnah_data(Ref(each_ref), talmud_tref, '', True, True, 'Missing from links', '')
        else:
            mishnah_data = get_mishnah_data(Ref(each_ref), 'No link', '', True, True, 'Missing from links', '')

        mishnah_list.append(mishnah_data)

    return mishnah_list


# This function flags any Mishnayot whose ratio of Hebrew text / German text
# is at least two standard deviations away from the mean in either direction.
def flag_if_length_out_of_stdev(mishnah_list, stdev, mean):
    for each_mishnah in mishnah_list:
        high = mean + 2 * stdev
        low = mean - 2 * stdev

        german_text = TextChunk._strip_itags(each_mishnah['german_text'])
        german_text = re.sub(r'<.*?>', '', german_text)
        hebrew_text = each_mishnah['hebrew_text']
        if len(german_text) > 0:
            cur_ratio = len(hebrew_text) / len(german_text)

            if cur_ratio > high:
                each_mishnah[
                    "length_flag"] += f"The ratio between the Hebrew and German word counts of this Mishnah is two standard deviations above the mean "
            elif cur_ratio < low:
                each_mishnah[
                    "length_flag"] += f"The ratio between the Hebrew and German word counts of this Mishnah is two standard deviations below the mean "


# This function calls the helper functions which
# resolve the obvious mismatch errors in the data
def process_data(mishnah_list):
    mishnah_list = merge_segments_of_mishnah(mishnah_list)
    mishnah_list = condense_blanks(mishnah_list)
    mishnah_list = add_empty(mishnah_list)
    mishnah_list = extract_joined_mishnahs(mishnah_list)
    mishnah_list = catch_edge_cases(mishnah_list)

    # ## Todo - remove?
    # for mishnah in mishnah_list:
    #     if mishnah['german_text'] == '':
    #         print(mishnah['mishnah_tref'])
    german_mean, german_stdev = mishnah_statistics(mishnah_list)
    flag_if_length_out_of_stdev(mishnah_list, stdev=german_stdev, mean=german_mean)
    return mishnah_list


### VALIDATION ####

def diff_german_text(mishnah_list):
    all_text = []

    ## Here?
    def action(segment_str, tref, he_tref, version):
        nonlocal all_text
        all_text.append(segment_str)

    bavli_indices = library.get_indexes_in_category("Bavli", full_records=True)
    for index in bavli_indices:
        german_talmud = Version().load(
            {"title": index.title, "versionTitle": 'Talmud Bavli. German trans. by Lazarus Goldschmidt, 1929 [de]'})
        if german_talmud:
            german_talmud.walk_thru_contents(action)
    print(f'len of gem = {len(all_text)}')
    for each_mishnah in mishnah_list:
        if each_mishnah['german_text'] not in all_text:
            print(each_mishnah['mishnah_tref'])


if __name__ == "__main__":
    mishnah_list = scrape_german_mishnah_text()
    mishnah_list = process_data(mishnah_list)
    # diff_german_text(mishnah_list)

    generate_csv_german_mishnah(mishnah_list)
