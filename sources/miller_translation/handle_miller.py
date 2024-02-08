import django

django.setup()

superuser_id = 171118
import csv
from sefaria.model import *
import re
from sefaria.tracker import modify_bulk_text
from bs4 import BeautifulSoup
from typing import List, Dict


new_verse_token = "$DIGIT_NEW_VERSE: "
new_chapter_token = "$DIGIT_NEW_CHAPTER: "
header_token = "$HEADER: "
comment_token = "$COMMENT: "
def get_list_of_verses_genesis():
    html_document = open(f"data/Genesis.html", 'r', encoding='utf-8').read()
    soup = BeautifulSoup(html_document, 'html.parser')
    soup = prepend_to_text_in_elements(soup, "TRANSLATION-SMALL-HEADINGS", comment_token)
    soup = prepend_to_text_in_elements(soup, "TRANSLATION-HEADINGS", header_token)
    soup = prepend_to_text_in_elements(soup, "CharOverride-3", new_verse_token)
    soup = prepend_to_text_in_elements(soup, "CharOverride-15", new_verse_token)
    soup = prepend_to_text_in_elements(soup, "CharOverride-2", new_chapter_token)
    soup = prepend_to_text_in_elements(soup, "_idGenDropcap-1", new_chapter_token)
    soup = prepend_to_text_in_elements(soup, "_idGenDropcap-4", new_chapter_token)
    soup = prepend_to_text_in_elements(soup, "CharOverride-14", new_chapter_token)
    soup = prepend_to_text_in_elements(soup, "CharOverride-16", new_chapter_token)
    soup = prepend_to_text_in_elements(soup, "CharOverride-13", new_chapter_token)

    soup = append_br_for_p(soup)


    # selected_elements = soup.find_all(class_=lambda x: x and (x.startswith("CharOverride-3") or x.startswith("CharOverride-4") or x.startswith("TRANSLATION-HEADINGS") or x.startswith("TRANSLATION-SMALL-HEADINGS")))
    # selected_elements = find_elements_with_prefix(soup, ["CharOverride-3", "CharOverride-4", "CharOverride-15", "TRANSLATION-HEADINGS", "TRANSLATION-SMALL-HEADINGS"])
    selected_elements = find_elements_with_prefix(soup, ["ParaOverride", "NEW-BULLET", "TRANSLATION-HEADINGS", "PEREK"])
    text_list = [element.text for element in selected_elements]
    clean_text = ''.join(text_list)
    clean_text = replace_double_digits(clean_text, new_verse_token)
    clean_text = replace_double_digits(clean_text, new_chapter_token)
    text_list = clean_text.split("$")
    text_list = [remove_br_from_end(line) for line in text_list]
    text_list = [item.strip() for item in text_list if item.strip()]
    text_list = [line for line in text_list if not line.startswith(new_chapter_token[1:])]
    return text_list


def get_list_of_verses_leviticus():
    html_document = open(f"data/Leviticus.html", 'r', encoding='utf-8').read()

    soup = BeautifulSoup(html_document, 'html.parser')

    header_classes = ["ORANGE-HEADING", "ORANGE-HEADING-BEFORE-AND-AFTER-BULET", "TRANSLATION-HEADINGS", "ORANGE-HAEDING-JUST-AFTER-BULET"]
    soup = prepend_token_to_classes(soup, header_classes, header_token)

    verse_classes = ["CharOverride-2", "CharOverride-6", "CharOverride-5", "CharOverride-10", "CharOverride-19", "CharOverride-15", "CharOverride-24"]
    soup = prepend_token_to_classes(soup, verse_classes, new_verse_token)

    chapter_classes = ["_idGenDropcap-1", "_idGenDropcap-2", "CharOverride-22", "CharOverride-9", "CharOverride-21", "CharOverride-18", "CharOverride-23"]
    soup = prepend_token_to_classes(soup, chapter_classes, new_chapter_token)

    soup = append_br_for_p(soup)

    selected_elements = find_elements_with_prefix(soup, ["ParaOverride", "NEW-BULLET", "TRANSLATION-HEADINGS", "PEREK", "ORANGE-HEADING", "BULLET-MITZVAH"])
    text_list = [element.text for element in selected_elements]

    clean_text = ''.join(text_list)
    clean_text = replace_double_digits(clean_text, new_verse_token)
    clean_text = replace_double_digits(clean_text, new_chapter_token)

    text_list = clean_text.split("$")
    text_list = [remove_br_from_end(line) for line in text_list]
    text_list = [item.strip() for item in text_list if item.strip() and not item.startswith(new_chapter_token[1:])]
    text_list = [line.replace("[]", "") for line in text_list]

    return text_list
def get_list_of_verses_numbers():
    html_document = open(f"data/Numbers.html", 'r', encoding='utf-8').read()

    soup = BeautifulSoup(html_document, 'html.parser')

    header_classes = ["ORANGE-HEADING", "ORANGE-HEADING-BEFORE-AND-AFTER-BULET", "TRANSLATION-HEADINGS", "ORANGE-HAEDING-JUST-AFTER-BULET"]
    soup = prepend_token_to_classes(soup, header_classes, header_token)

    verse_classes = ["CharOverride-9", "CharOverride-2", "CharOverride-8", "CharOverride-35", "CharOverride-12"]
    soup = prepend_token_to_classes(soup, verse_classes, new_verse_token)

    chapter_classes = ["CharOverride-10", "CharOverride-1", "_idGenDropcap-1", "_idGenDropcap-3", "CharOverride-25"]
    soup = prepend_token_to_classes(soup, chapter_classes, new_chapter_token)

    soup = append_br_for_p(soup)

    selected_elements = find_elements_with_prefix(soup, ["ParaOverride", "NEW-BULLET", "TRANSLATION-HEADINGS", "PEREK", "ORANGE-HEADING", "BULLET-MITZVAH"])
    text_list = [element.text for element in selected_elements]

    clean_text = ''.join(text_list)
    clean_text = replace_double_digits(clean_text, new_verse_token)
    clean_text = replace_double_digits(clean_text, new_chapter_token)

    text_list = clean_text.split("$")
    text_list = [remove_br_from_end(line) for line in text_list]
    text_list = [item.strip() for item in text_list if item.strip() and not item.startswith(new_chapter_token[1:])]
    text_list = [line.replace("[]", "") for line in text_list]

    return text_list

def get_list_of_verses_deuteronomy():
    html_document = open(f"data/Deuteronomy.html", 'r', encoding='utf-8').read()

    soup = BeautifulSoup(html_document, 'html.parser')

    header_classes = ["ORANGE-HEADING", "ORANGE-HEADING-BEFORE-AND-AFTER-BULET", "TRANSLATION-HEADINGS", "ORANGE-HAEDING-JUST-AFTER-BULET"]
    soup = prepend_token_to_classes(soup, header_classes, header_token)

    verse_classes = ["CharOverride-2", "CharOverride-27", "CharOverride-16",
                     "CharOverride-7", "CharOverride-31"]
    soup = prepend_token_to_classes(soup, verse_classes, new_verse_token)

    chapter_classes = ["CharOverride-1", "_idGenDropcap-2","_idGenDropcap-1",
                       "CharOverride-23", "CharOverride-20", "CharOverride-22"]
    soup = prepend_token_to_classes(soup, chapter_classes, new_chapter_token)

    soup = append_br_for_p(soup)

    selected_elements = find_elements_with_prefix(soup, ["ParaOverride", "NEW-BULLET", "TRANSLATION-HEADINGS", "PEREK", "ORANGE-HEADING", "BULLET-MITZVAH"])
    text_list = [element.text for element in selected_elements]

    clean_text = ''.join(text_list)
    clean_text = replace_double_digits(clean_text, new_verse_token)
    clean_text = replace_double_digits(clean_text, new_chapter_token)

    text_list = clean_text.split("$")
    text_list = [remove_br_from_end(line) for line in text_list]
    text_list = [item.strip() for item in text_list if item.strip() and not item.startswith(new_chapter_token[1:])]
    text_list = [line.replace("[]", "") for line in text_list]

    return text_list
def get_list_of_verses_exodus():
    html_document = open(f"data/Exodus.html", 'r', encoding='utf-8').read()

    soup = BeautifulSoup(html_document, 'html.parser')

    header_classes = ["ORANGE-HEADING", "ORANGE-HEADING-BEFORE-AND-AFTER-BULET", "TRANSLATION-HEADINGS", "ORANGE-HAEDING-JUST-AFTER-BULET"]
    soup = prepend_token_to_classes(soup, header_classes, header_token)

    verse_classes = ["CharOverride-4", "CharOverride-6", "CharOverride-36", "CharOverride-20", "CharOverride-41", "CharOverride-34"]
    soup = prepend_token_to_classes(soup, verse_classes, new_verse_token)

    chapter_classes = ["CharOverride-3", "CharOverride-11", "CharOverride-27"]
    soup = prepend_token_to_classes(soup, chapter_classes, new_chapter_token)

    soup = append_br_for_p(soup)

    selected_elements = find_elements_with_prefix(soup, ["ParaOverride", "NEW-BULLET", "TRANSLATION-HEADINGS", "PEREK", "ORANGE-HEADING", "BULLET-MITZVAH"])
    text_list = [element.text for element in selected_elements]

    clean_text = ''.join(text_list)
    clean_text = replace_double_digits(clean_text, new_verse_token)
    clean_text = replace_double_digits(clean_text, new_chapter_token)

    text_list = clean_text.split("$")
    text_list = [remove_br_from_end(line) for line in text_list]
    text_list = [item.strip() for item in text_list if item.strip() and not item.startswith(new_chapter_token[1:])]
    text_list = [line.replace("[]", "") for line in text_list]

    return text_list

def remove_br_from_end(input_string):
    if input_string.strip().endswith("<br>"):
        return input_string[:-4].strip()
    else:
        return input_string
def prepend_token_to_classes(soup, classes, token):
    for class_name in classes:
        soup = prepend_to_text_in_elements(soup, class_name, token)
    return soup
def find_elements_with_prefix(soup, class_prefixes):
    selected_elements = soup.find_all(class_=lambda x: x and any(x.startswith(prefix) for prefix in class_prefixes))
    return selected_elements
def clean_line(line):
    line = replace_double_digits(line, new_verse_token)
    return line
def replace_double_digits(input_string, token):
    token_escape = re.escape(token)
    pattern = token_escape+r'(\d+)'+token_escape+r'(\d+)'
    # pattern = r'DIGIT_NEW_VERSE: (\d+)DIGIT_NEW_VERSE: (\d+)'
    result_string = re.sub(pattern, token + r'\1\2', input_string)
    return result_string

def replace_double_digit_new_chapter(input_string):
    pattern = new_chapter_token+r'(\d+)'+new_chapter_token+r'(\d+)'
    result_string = re.sub(pattern, new_verse_chapter + r'\1\2', input_string)

    return result_string
def prepend_to_text_in_elements(soup, class_name, prepended_text):
    selected_elements = soup.find_all(class_=class_name)

    for element in selected_elements:
        if element.string and element.string.strip():
            element.string.replace_with(prepended_text + element.get_text().strip())

    return soup
def append_br_for_p(soup):
    selected_elements = soup.find_all("p")

    for element in selected_elements:
        if element.string and element.string.strip():
            element.string.replace_with(element.get_text().strip() + "<br>")

    return soup

def count_elements_with_class(html_document, class_name):
    soup = BeautifulSoup(html_document, 'html.parser')
    selected_elements = soup.find_all(class_=class_name)

    return len(selected_elements)

def marked_list_to_map(text_list: List[str], book_name: str):
    text_map = {}
    chapter = 0
    for index, line in enumerate(text_list):
        if line.startswith(new_verse_token[1:]):
            cleaned_line = line.replace(new_verse_token[1:], '')
            verse_num, cleaned_line = extract_and_delete_first_number(cleaned_line)
            if verse_num == 1:
                chapter += 1
            text_map[generate_tref(book_name, chapter, verse_num)] = cleaned_line

        if line.startswith(header_token[1:]):
            line = line.replace(header_token[1:], '')
            text_list[index+1] = insert_string_after_number("<b>" + line + "</b>" + "<br>", text_list[index+1])
    for key in text_map:
        text_map[key] = final_clean(text_map[key])

    return text_map

def get_next_element(my_list, current_element):
    try:
        index_of_current = my_list.index(current_element)
        next_index = index_of_current + 1

        # Check if there is a next element
        if next_index < len(my_list):
            return my_list[next_index]
        else:
            # If there is no next element, you may choose to return None or handle it differently
            return None
    except ValueError:
        # Handle the case where the current_element is not in the list
        print(f"{current_element} is not in the list.")
        return None
def insert_string_after_number(string1, string2):
    # Find the index of the first digit in string2
    index_of_first_digit = next((i for i, char in enumerate(string2) if char.isdigit()), None)

    if index_of_first_digit is not None:
        # Find the index of the last digit in the number in string2
        index_of_last_digit = index_of_first_digit + 1
        while index_of_last_digit < len(string2) and string2[index_of_last_digit].isdigit():
            index_of_last_digit += 1

        # Insert string1 after the first number in string2
        result = string2[:index_of_last_digit] + string1 + string2[index_of_last_digit:]
        return result
    else:
        # If there is no digit in string2, just concatenate the two strings
        return string2 + string1

def extract_and_delete_regex(pattern, input_string):
    match = re.search(pattern, input_string)

    if match:
        extracted_text = match.group(0)
        modified_string = re.sub(pattern, '', input_string)
        return extracted_text, modified_string
    else:
        return None, input_string


def extract_and_delete_first_number(s):
    match = re.search(r'\d+', s)

    if match:
        matched_number = match.group()
        number = int(matched_number)
        result_string = re.sub(r'\d+', '', s, 1)
        return number, result_string.strip()
    else:
        return None, s
def get_first_number(s):
    match = re.search(r'\d+', s)
    if match:
        return int(match.group())
    else:
        return None

def generate_tref(book_name: str, chapter, verse_num):
    return book_name + " " + str(chapter) + ":" + str(verse_num)
def ingest_version(book_map: Dict):
    book_name = list(book_map.keys())[0].split()[0]
    index = library.get_index(book_name)
    cur_version = VersionSet({'title': book_name,
                              "versionTitle" : "Version Title: Gutnick edition Chumash, by Chaim Miller, 2011"})

    if cur_version.count() > 0:
        cur_version.delete()
        print("deleted existing version")
    chapter = index.nodes.create_skeleton()
    version = Version({"versionTitle": "Version Title: Gutnick edition Chumash, by Chaim Miller, 2011",
                       "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH990022868150205171/NLI",
                       "title": book_name,
                       "language": "en",
                       "chapter": chapter,
                       "digitizedBySefaria": True,
                       "license": "PD",
                       "status": "locked"
                       })
    modify_bulk_text(superuser_id, version, book_map)

def find_first_difference(list1, list2):
    min_len = min(len(list1), len(list2))

    for i in range(min_len):
        if list1[i] != list2[i]:
            return i

    # If the lists are of different lengths, return the index of the first differing element
    return min_len if len(list1) != len(list2) else None
def final_clean(input_string):
    pattern = re.compile(r'([a-zA-Z]):([a-zA-Z])')

    result_string = pattern.sub(r'\1: \2', input_string)

    if result_string != input_string:
        print("Match found:", input_string)

    pattern = re.compile(r'\b([a-zA-Z])\.([a-zA-Z])\b')

    result_string = pattern.sub(r'\1. \2', result_string)

    if result_string != input_string:
        print("Match found:", input_string)

    # if "But when Samson will be overcome by his enemies" in input_string:
    #     halt = True

    # result_string = re.sub(r'\[.*?\]', '', result_string).strip()
    #
    # if result_string != input_string:
    #     print("Match found:", input_string)

    result_string = result_string.replace("[MAFTIR]", "").strip()
    if result_string != input_string:
        print("Match found:", input_string)

    result_string = result_string.replace("<br></b><br>", "</b><br>").strip()

    if result_string != input_string:
        print("Match found:", input_string)

    # pattern = re.compile(r'([a-zA-Z])-([a-zA-Z])')
    # result_string = pattern.sub(r'\1- \2', input_string)
    # if result_string != input_string:
    #     print("Match found:", input_string)

    return result_string

def handle_books():
    text_list = get_list_of_verses_genesis()
    map = marked_list_to_map(text_list, "Genesis")
    ingest_version(map)

    text_list = get_list_of_verses_exodus()
    map = marked_list_to_map(text_list, "Exodus")
    ingest_version(map)

    text_list = get_list_of_verses_leviticus()
    map = marked_list_to_map(text_list, "Leviticus")
    ingest_version(map)

    text_list = get_list_of_verses_numbers()
    map = marked_list_to_map(text_list, "Numbers")
    ingest_version(map)

    text_list = get_list_of_verses_deuteronomy()
    map = marked_list_to_map(text_list, "Deuteronomy")
    ingest_version(map)


if __name__ == '__main__':
    print("hello world")
    handle_books()







    print("end")



