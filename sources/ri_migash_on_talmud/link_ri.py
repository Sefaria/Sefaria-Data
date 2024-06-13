import django

django.setup()
from tqdm import tqdm
superuser_id = 171118
import csv
import re
from sefaria.model import *
from sefaria.utils.talmud import daf_to_section, section_to_daf
from typing import List
from pprint import pprint
import copy

def list_of_dict_to_links(dicts):
    list_of_dicts = []
    for d in dicts:
        list_of_dicts.append(Link(d))
    return list_of_dicts
def insert_links_to_db(list_of_dict_links):
    list_of_links = list_of_dict_to_links(list_of_dict_links)
    for l in list_of_links:
        try:
            l.save()
        except Exception as e:
            print(e)
def get_daf_key(row):
    daf = row['Daf']
    volume_num = len(re.search(r"Volume (I+),", daf).group(1))
    daf_num = daf_to_section(re.search(r", (\d+[ab])$", daf).group(1))
    return volume_num*1000 + daf_num

def simple_tokenizer(text):
    """
    A simple tokenizer that splits text into tokens by whitespace,
    and removes apostrophes and periods from the tokens.
    """

    def remove_nikkud(hebrew_string):
        # Define a regular expression pattern for Hebrew vowel points
        nikkud_pattern = re.compile('[\u0591-\u05BD\u05BF-\u05C2\u05C4\u05C5\u05C7]')

        # Use the sub method to replace vowel points with an empty string
        cleaned_string = re.sub(nikkud_pattern, '', hebrew_string)

        return cleaned_string
    # Replace apostrophes and periods with empty strings
    text = text.replace("'", "")
    text = text.replace(".", "")
    text = text.replace("׳", "")
    text = text.replace("–", "")
    text = text.replace(";", "")
    text = remove_nikkud(text)

    # Split the text into tokens by whitespace
    tokens = text.split()
    return tokens
def dher(text):
    dh = "$$$$$$$$$$$$$$$$$$"
    match = re.search(r'<b>(.*?)</b>', text)
    if match:
        if len(match.group(1).split()) >= 2:
            dh = match.group(1)
    return dh


def get_rows(prefix, node):
    temp_rows = []
    starting_int = daf_to_section(node.startingAddress)
    for i, tref in enumerate(node.refs):
        curr_daf = section_to_daf(starting_int+i)
        # temp_rows += [{"Daf": f"{prefix}, {curr_daf}", "URL": "https://sefaria.org/" + Ref(tref).url()}]
        temp_rows += [{"Daf": f"{prefix}, {curr_daf}", "Siman": tref}]
    return temp_rows

def links_to_csv(list_of_links, filename="output.csv"):
    tuples = []
    tuples.append(("Yahel Ref", "Zohar Ref", "Yahel Text", "Zohar Text"))
    for link in list_of_links:
        tuples += [(link["refs"][0], link["refs"][1], Ref(link["refs"][0]).text("he").text, Ref(link["refs"][1]).text("he").text)]
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(tuples)

def get_and_strip_last_number(s):
    # Search for the last occurrence of a number in the string
    match = re.search(r'\d+', s[::-1])

    if match:
        # Extract the matched number
        last_number = int(match.group()[::-1])

        # Strip the matched number from the original string
        stripped_string = s[:-len(str(last_number))]

        return last_number, stripped_string
    else:
        # Return None if no number is found
        return None, s
def infer_logical_links(list_of_links):
    list_of_links_with_inferred = []
    # Iterate over consecutive elements
    for i in range(len(list_of_links) - 1):
        current_link = list_of_links[i]
        next_link = list_of_links[i + 1]
        list_of_links_with_inferred.append(current_link)
        current_seg_num, current_sec_tref = get_and_strip_last_number(current_link["refs"][0])
        next_seg_num, next_sec_tref = get_and_strip_last_number(next_link["refs"][0])
        if current_sec_tref == next_sec_tref and next_seg_num - current_seg_num == 2\
                and current_link["refs"][1] == next_link["refs"][1]:
            # print("logic")
            inferred_link = copy.deepcopy(current_link)
            inferred_link["refs"][0] = current_sec_tref + str(current_seg_num+1)
            # print("inferred: ")
            print(inferred_link["refs"][0])
            list_of_links_with_inferred.append(inferred_link)
    list_of_links_with_inferred.append(list_of_links[-1])
    return list_of_links_with_inferred

def remove_duplicates_ordered(input_list):
    seen = set()
    result_list = []

    for item in input_list:
        if item not in seen:
            seen.add(item)
            result_list.append(item)

    return result_list


def infer_links(ri_amud, talmud_amud):
    from sources.functions import match_ref_interface
    segs = Ref(ri_amud).all_segment_refs()
    comments = [seg.text("he").text for seg in segs]
    matches = match_ref_interface(talmud_amud, ri_amud,
                             comments, simple_tokenizer, dher)
    return matches

def match_commentary():
    daf_siman_map = create_daf_siman_map()
    yahel_sec_trefs = get_yahel_sec_trefs()
    yahel_dafXzohar_tref_list = generate_yahel_dafXzohar_tref_list(daf_siman_map, yahel_sec_trefs)

    print("hi")
    links = []
    look_side_ways_links = []
    for yahel_daf, zohar_tref in yahel_dafXzohar_tref_list:
        matches = infer_links(yahel_daf, zohar_tref)

        # missing_links = get_missing_links(yahel_daf, matches)
        zohar_tref_for_previous_daf = get_previous_value(yahel_dafXzohar_tref_list, yahel_daf)
        zohar_tref_for_next_daf = get_next_value(yahel_dafXzohar_tref_list, yahel_daf)
        print(zohar_tref_for_previous_daf)
        more_matches = []
        if zohar_tref_for_previous_daf:
            more_matches += infer_links(yahel_daf, zohar_tref_for_previous_daf)
        if zohar_tref_for_next_daf:
            more_matches += infer_links(yahel_daf, zohar_tref_for_next_daf)
        only_new_matches = get_new_matches(more_matches, matches)
        if only_new_matches:
            halt = 1
        matches += only_new_matches
        look_side_ways_links += only_new_matches





        links += matches
    links = infer_logical_links(links)
    # print("second iteration:")
    # links = infer_logical_links(links)
    links_to_csv(links, filename="output2.csv")
    sideways_refs = [link["refs"] for link in look_side_ways_links]
    pprint(sideways_refs)
    insert_links_to_db(links)

def get_validation_set(csv_filename):
    val_set = []
    with open(csv_filename, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            val_set.append(row)
    return val_set



if __name__ == '__main__':
    print("hello world")
    validation_set = get_validation_set("bava_batra_validation.csv")
    ri_bava_batra_amudim_refs = library.get_index("Ri Migash on Bava Batra").all_section_refs()
    for ri_amud_ref in ri_bava_batra_amudim_refs:
        talmud_amud_ref = Ref(ri_amud_ref.tref.replace("Ri Migash on ", ""))
        infer_links(ri_amud_ref.tref, talmud_amud_ref.tref)

    print("end")


