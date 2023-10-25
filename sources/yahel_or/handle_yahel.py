import django

django.setup()

superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
from sefaria.helper.schema import insert_last_child, reorder_children
from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
from sefaria.helper.category import create_category
from sefaria.system.database import db
from bs4 import BeautifulSoup
import os
import re


# import time


def post_indices():
    from sources.functions import post_index, post_term
    yahel_or_term = {"name": "Yahel Ohr", "titles": [{"lang": "en", "text": "Yahel Ohr", "primary": True},
                                        {"lang": "he", "text": "יהל אור", "primary": True}], "scheme": "toc_categories"}
    # post_term(yahel_or_term, server="https://yahel-ohr.cauldron.sefaria.org")
    nefesh_david_index = post_index({'title': 'Nefesh David on Zohar'}, server="https://www.sefaria.org.il", method="GET")
    yahel_or_index = nefesh_david_index
    yahel_or_index["title"] = "Yahel Ohr on Zohar"
    yahel_or_index["schema"]["titles"] = [{'lang': 'en', 'text': 'Yahel Ohr'}, {'lang': 'he', 'primary': True, 'text': 'יהל אור על ספר הזהר'}, {'lang': 'he', 'text': 'יהל אור על הזהר'}, {'lang': 'he', 'text': 'יהל אור'}, {'lang': 'en', 'primary': True, 'text': 'Yahel Ohr on Zohar'}]
    yahel_or_index["schema"]["key"] = 'Yahel Ohr on Zohar'
    del yahel_or_index['enDesc']
    del yahel_or_index['heDesc']
    del yahel_or_index["enShortDesc"]
    del yahel_or_index["heShortDesc"]
    yahel_or_index['collective_title'] = "Yahel Ohr"
    post_index(yahel_or_index, server="https://yahel-ohr.cauldron.sefaria.org")
    # post_index(yahel_or_index)

def ingest_yahel(book_map):
    index = library.get_index("Yahel Ohr on Zohar")
    cur_version = VersionSet({'title': "Yahel Ohr on Zohar",
                              "versionTitle" : "Vilna 1882"})

    if cur_version.count() > 0:
        cur_version.delete()
        print("deleted existing version")
    chapter = index.nodes.create_skeleton()
    version = Version({"versionTitle": "Vilna 1882",
                       "versionSource": "https://he.wikisource.org/wiki/%D7%99%D7%94%D7%9C_%D7%90%D7%95%D7%A8",
                       "title": "Yahel Ohr on Zohar",
                       "language": "he",
                       "chapter": chapter,
                       "digitizedBySefaria": True,
                       "license": "PD",
                       "status": "locked"
                       })
    modify_bulk_text(superuser_id, version, book_map)
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
def generate_sublists(input_list, foo, key_naming_logic):
    result_dict = {}
    current_key = None
    current_sublist = []

    for element in input_list:
        if foo(element):
            if current_key is not None:
                result_dict[current_key] = current_sublist
                current_sublist = []  # Reset the sublist when a new key is found
            current_key = key_naming_logic(element)
        else:
            current_sublist.append(element)

    if current_key is not None:
        result_dict[current_key] = current_sublist

    return result_dict
# Mikdash_Melekh_on_Zohar.1.15a.10

def a_tag_text_to_tref(a_tag_text, prefix):
    daf = str(compute_gematria(get_next_word(a_tag_text, "דף")))
    amud = a_tag_text.split()[-1]
    if amud is None:
        halt = True
    if "א" in amud or "." in amud:
        amud = 'a'
    elif "ב" in amud or ":" in amud:
        amud = 'b'
    else:
        print("Discrepancy!")
    return prefix + " " + daf + amud

def modify_dict_keys(map, prefix):
    new_dict = {}
    for old_key, value in map.items():
        # Modify the key using the a_tag_text_to_tref function
        new_key = a_tag_text_to_tref(old_key, prefix)

        # Add the key-value pair to the new dictionary
        new_dict[new_key] = value

    return new_dict
def flatten_dictionary(original_dict):
    new_dict = {}

    for key, value_list in original_dict.items():
        for index, element in enumerate(value_list):
            new_key = f"{key}:{index+1}"
            new_dict[new_key] = element

    return new_dict

def get_text_with_bold_tags(element):
    result = ''
    for item in element.contents:
        if isinstance(item, str):
            result += item
        elif item.name == 'b':
            result += f'<b>{get_text_with_bold_tags(item)}</b>'
    result = result.replace("<p>", '').replace("</p>",'')
    return result

def clean_html_except_b_and_small(element):

    # Find all tags except for <b> and <small> and extract their contents
    allowed_tags = ['b', 'small', 'br']
    for tag in element.find_all(True):
        if tag.name not in allowed_tags:
            tag.unwrap()  # Remove the tag but keep its contents

    # Get the cleaned HTML string
    cleaned_html = str(element).replace("<p>",'').replace("</p>",'')
    if "הנצנים דא" in cleaned_html:
        halt = True
    cleaned_html = cleaned_html[len("<br>"):] if cleaned_html.startswith("<br>") else cleaned_html
    cleaned_html = cleaned_html[len("<br/>"):] if cleaned_html.startswith("<br/>") else cleaned_html


    return cleaned_html

def eliminate_extra_spaces_after_dibur_hamatchil(s):
    return s.replace("   ", " ")
def apply_function_to_values(input_dict, foo):
    result_dict = {}

    for key, value in input_dict.items():
        result_dict[key] = foo(value)

    return result_dict
def general_parse(html_path, prefix):
    with open(html_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    elements = []
    for element in soup.find_all(['p', 'a']):
        elements.append(element if (element.name == 'p' and not element.get_text().isspace()) or (element.name == 'a' and element.get_text().startswith('דף') and "דף השיחה" not in element.get_text() and element.get_text() not in {"דף", "דף אקראי"}) else None)
    elements = list(filter(lambda x: x is not None, elements))

    map = generate_sublists(elements, lambda x: (x.name == 'a'), lambda x: x.get_text())
    # Create a new dictionary with modified keys
    map = flatten_dictionary(modify_dict_keys(map, prefix))
    map = apply_function_to_values(map, clean_html_except_b_and_small)
    map = apply_function_to_values(map, eliminate_extra_spaces_after_dibur_hamatchil)

    halt = True
    return map

if __name__ == '__main__':
    print("hello world")
    post_indices()
    text_map = {}
    text_map = {**text_map, **general_parse('htmls/ספר_בראשית.html', "Yahel Ohr on Zohar 1")}
    text_map = {**text_map, **general_parse('htmls/ספר_שמות_חלק_א.html', "Yahel Ohr on Zohar 2")}
    text_map = {**text_map, **general_parse('htmls/ספר_שמות_חלק_ב.html', "Yahel Ohr on Zohar 2")}
    text_map = {**text_map, **general_parse('htmls/ספר_שמות_חלק_ג.html', "Yahel Ohr on Zohar 2")}
    text_map = {**text_map, **general_parse('htmls/ספר_ויקרא.html', "Yahel Ohr on Zohar 3")}
    text_map = {**text_map, **general_parse('htmls/ספר_במדבר_חלק_א.html', "Yahel Ohr on Zohar 3")}
    text_map = {**text_map, **general_parse('htmls/ספר_במדבר_חלק_ב.html', "Yahel Ohr on Zohar 3")}
    text_map = {**text_map, **general_parse('htmls/ספר_דברים.html', "Yahel Ohr on Zohar 3")}
    text_map = {**text_map, **general_parse('htmls/הקדמת_הזהר.html', "Yahel Ohr on Zohar 1")}
    text_map = {**text_map, **general_parse('htmls/ספר_בראשית_-_השמטות.html', "Yahel Ohr on Zohar 1")}
    ingest_yahel(text_map)





    print("end")











