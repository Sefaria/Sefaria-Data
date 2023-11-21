import django

django.setup()

superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
import re
# from sefaria.helper.schema import insert_last_child, reorder_children
# from sefaria.helper.schema import remove_branch
# from sefaria.tracker import modify_bulk_text
# from sefaria.helper.category import create_category
# from sefaria.system.database import db



# def list_of_dict_to_links(dicts):
#     list_of_dicts = []
#     for d in dicts:
#         list_of_dicts.append(Link(d))
#     return list_of_dicts

def insert_links_to_db(list_of_links):
    for l in list_of_links:
        try:
            l.save()
        except Exception as e:
            print(e)


def compute_gematria(word):
    # Define the numerical values of each letter
    gematria = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}

    # Compute the Gematria of the word
    total = 0
    for letter in word:
        if letter in gematria:
            total += gematria[letter]
    return total
def get_next_word(input_string, w):
    words = input_string.split()

    try:
        index = words.index(w)
        # Check if 'w' is not the last word in the string
        if index < len(words) - 1:
            return words[index + 1]
        else:
            return None  # 'w' is the last word in the string
    except ValueError:
        return None  # 'w' is not found in the string


def extract_last_number(input_string):
    # Use regular expression to find all numbers in the string
    numbers = re.findall(r'\d+', input_string)

    # Check if any numbers were found
    if numbers:
        # Return the last number found in the string
        return int(numbers[-1])
    else:
        # Return None if no numbers are found
        return None

def find_greatest_number(prefix, my_dict):
    greatest_number = None

    for key in my_dict.keys():
        if key.startswith(prefix):
            # Extract the numeric part of the key
            numeric_part = extract_last_number(key[len(prefix):])

            try:
                # Convert the numeric part to an integer
                current_number = int(numeric_part)

                # Update greatest_number if the current_number is greater
                if greatest_number is None or current_number > greatest_number:
                    greatest_number = current_number
            except ValueError:
                # Ignore keys with non-numeric suffixes
                pass

    return greatest_number if greatest_number is not None else 0
def partition_list(a, f):
    result = []
    current_sublist = []

    for i, element in enumerate(a):
        if i == 0 or f(a[i-1], element):
            current_sublist.append(element)
        else:
            result.append(current_sublist)
            current_sublist = [element]

    if current_sublist:
        result.append(current_sublist)

    return result
def extract_bold_inner_text(input_string):
    # Define the regex pattern for matching the bold tag and its inner text
    pattern = re.compile(r'<b>(.*?)</b>', re.DOTALL)

    # Use the findall method to find all matches in the input string
    matches = pattern.findall(input_string)

    # Check if there is at least one match
    if matches:
        # Return the inner text of the first match
        return matches[0]
    else:
        # Return None if no match is found
        return None
def start_new_sublist_only_if(ref1, ref2):
    # Replace this condition with your own logic
    refs_are_consecutive = (ref1.next_segment_ref() == ref2)
    cur_seg_text =  ref2.text("he").text
    cur_seg_starts_with_bold = cur_seg_text.startswith("<b>")
    if cur_seg_starts_with_bold:
        starting_bold_text = extract_bold_inner_text(ref2.text("he").text).strip()
        starting_bold_text_ends_with_dot =  starting_bold_text.endswith(".")
        starting_bold_text_has_many_words = len(starting_bold_text.split()) >= 2

    is_new_dh = cur_seg_starts_with_bold and (starting_bold_text_ends_with_dot or starting_bold_text_has_many_words)
    return refs_are_consecutive and not is_new_dh

def creat_bahya_link(bahya_tref, torah_tref):
    link = Link({
        "refs": [
            torah_tref,
            bahya_tref
        ],
        "generated_by": None,
        "type": "commentary",
        "auto": False
    })
    return link


def bahya_tref_to_torah_tref(input_string):
    # Find the index of the first comma
    first_comma_index = input_string.find(',')

    # Find the index of the last colon
    last_colon_index = input_string.rfind(':')

    # Extract the substring between the first comma and the last colon
    result = input_string[first_comma_index + 1:last_colon_index].strip()

    return result
if __name__ == '__main__':
    print("hello world")
    bahya_segment_refs = library.get_index('Rabbeinu Bahya').all_segment_refs()
    bahya_segment_refs = [ref for ref in bahya_segment_refs if "Introduction" not in ref.tref]
    match_vector = []
    unmatched_commentary_refs = []
    for seg_ref in bahya_segment_refs:
        commentary_links = LinkSet(seg_ref)
        filtered = [link for link in commentary_links.array() if link.type == "Commentary" or link.type == "commentary"]
        match_vector += [1 if filtered else 0]
        unmatched_commentary_refs += [seg_ref] if not filtered else []

    # with open("bayha_unlinked_refs.csv", mode='w', newline='') as file:
    #     csv.writer(file).writerows([[ref.tref] for ref in unmatched_commentary_refs])

    partition = partition_list(unmatched_commentary_refs, start_new_sublist_only_if)
    # print(f"score: {sum(match_vector)/len(match_vector)}")
    new_links = []
    for sublist in partition:
        new_links += [creat_bahya_link(sublist[0].to(sublist[-1]).tref, bahya_tref_to_torah_tref(sublist[0].tref))]

    insert_links_to_db(new_links)
    print("end")