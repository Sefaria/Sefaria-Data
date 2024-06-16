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
    # match = re.search(r'<b>(.*?)</b>', text)
    # if match:
    #     if len(match.group(1).split()) >= 2:
    #         dh = match.group(1)
    words = text.split(" ")[:10]
    cutoff_index = -1
    for index, word in enumerate(words):
        if word[-1] == '.' or word in {"וכו'", "פירש", "פירוש",}:
            cutoff_index = index
            break
    if cutoff_index > -1:
          words = words[:cutoff_index+1]
    dh = " ".join(words)
    return dh




def links_to_csv(list_of_links, filename="output.csv"):
    tuples = []
    tuples.append(("Ri Migash Ref", "Talmud Ref", "Ri Migash Text", "Talmud Text", "URL"))
    def create_data_tuple(link):
        return (link["refs"][0], link["refs"][1], Ref(link["refs"][0]).text("he").text, Ref(link["refs"][1]).text("he").text,
         f"https://new-shmuel.cauldron.sefaria.org/{Ref((link['refs'][0])).url()}?lang=he&p2={Ref(link['refs'][1]).url()}&?lang2=he")
    def create_only_base_ref_tuple(base_ref):
        return (base_ref, "", "", "", f"https://new-shmuel.cauldron.sefaria.org/{Ref(base_ref).url()}?lang=he")

    for ri_seg_ref in library.get_index("Ri Migash on Bava Batra").all_segment_refs():
        matching_links = [link for link in list_of_links if Ref(link["refs"][0]) == ri_seg_ref]
        matching_link = matching_links[0] if matching_links else None
        if matching_link:
            tuples.append(create_data_tuple(matching_link))
        else:
            tuples.append(create_only_base_ref_tuple(ri_seg_ref.normal()))
    # for link in list_of_links:
    #     tuples += [create_data_tuple(link)]
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
    talmud_amud_extended = (Ref(talmud_amud).to(Ref(talmud_amud).all_segment_refs()[-1].next_segment_ref())).normal()
    matches = match_ref_interface(talmud_amud_extended, ri_amud,
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
            val_set.append((Ref(row[0]).normal(),Ref(row[1]).normal()))
    return val_set


def get_f_score(golden_standard, predictions):
    """
    Calculate the F-score given the golden standard and predictions.

    Parameters:
    golden_standard (list): The list of true labels.
    predictions (list): The list of predicted labels.

    Returns:
    float: The F-score.
    """

    # Convert to sets to handle the case of unordered lists
    golden_standard_set = set(golden_standard)
    predictions_set = set(predictions)

    # Calculate true positives, false positives, and false negatives
    true_positives = len(golden_standard_set.intersection(predictions_set))
    false_positives = len(predictions_set - golden_standard_set)
    false_negatives = len(golden_standard_set - predictions_set)

    # Calculate precision and recall
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0

    # Calculate F-score
    if precision + recall == 0:
        return 0.0
    f_score = 2 * (precision * recall) / (precision + recall)

    return f_score, recall, precision

def print_false_negatives(golden_standard, predictions):
    golden_standard_set = set(golden_standard)
    predictions_set = set(predictions)
    false_negatives_set = golden_standard_set - predictions_set
    print("False Negatives:")
    for match in false_negatives_set:
        #http://localhost:8000/Genesis.5.1?lang=he&with=Rashi&lang2=he
        # print(f"https://new-shmuel.cauldron.sefaria.org/{Ref(match[0]).url()}?lang=he&p2={Ref(match[1]).url()}&?lang2=he")
        print(f"http://localhost:8000/{Ref(match[0]).url()}?lang=he&p2={Ref(match[1]).url()}&?lang2=he")
def print_false_positives(golden_standard, predictions):
    golden_standard_set = set(golden_standard)
    predictions_set = set(predictions)
    false_positives = predictions_set - golden_standard_set
    print("False Positives:")
    for match in false_positives:
        #http://localhost:8000/Genesis.5.1?lang=he&with=Rashi&lang2=he
        print(f"http://localhost:8000/{Ref(match[0]).url()}?lang=he&p2={Ref(match[1]).url()}&?lang2=he")
def score_matches(validation_set):
    # first_ri_tref = validation_set[0][0]
    last_ri_tref = validation_set[-1][0]
    index_of_colon = last_ri_tref.find(':')
    last_ri_amud_tref = last_ri_tref[0:index_of_colon]
    ri_bava_batra_amudim_refs = library.get_index("Ri Migash on Bava Batra").all_section_refs()
    matches = []
    for ri_amud_ref in ri_bava_batra_amudim_refs:
        talmud_amud_ref = Ref(ri_amud_ref.tref.replace("Ri Migash on ", ""))
        matches += infer_links(ri_amud_ref.tref, talmud_amud_ref.tref)
        if ri_amud_ref == Ref(last_ri_amud_tref):
            break
    matches_pairs = []
    for link in matches:
        matches_pairs.append((Ref(link['refs'][0]).normal(), Ref(link['refs'][1]).normal()))
    f_score, recall, precision = get_f_score(validation_set, matches_pairs)
    print(f"f_score: {f_score}")
    print(f"recall: {recall}")
    print(f"precision: {precision}")
    print_false_negatives(validation_set, matches_pairs)
    print_false_positives(validation_set, matches_pairs)

def link_ri_bava_batra():
    ri_bava_batra_amudim_refs = library.get_index("Ri Migash on Bava Batra").all_section_refs()
    matches = []
    for ri_amud_ref in ri_bava_batra_amudim_refs:
        talmud_amud_ref = Ref(ri_amud_ref.tref.replace("Ri Migash on ", ""))
        matches += infer_links(ri_amud_ref.tref, talmud_amud_ref.tref)
    return matches
if __name__ == '__main__':
    print("hello world")
    # validation_set = get_validation_set("bava_batra_validation.csv")
    # score_matches(validation_set)
    links = link_ri_bava_batra()
    links_to_csv(links)


    print("end")


