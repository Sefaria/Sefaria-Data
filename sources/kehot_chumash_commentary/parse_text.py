from __future__ import annotations

import django
django.setup()
from sefaria.model import *
from sources.functions import *
from bs4 import BeautifulSoup

title = "The Kehot Chumash; A Chasidic Commentary"



num_to_book_map = {
    **{i: 'Genesis' for i in range(1, 13)},
    **{i: 'Exodus' for i in range(13, 24)},
    **{i: 'Leviticus' for i in range(24, 34)},
    **{i: 'Numbers' for i in range(34, 44)},
    **{i: 'Deuteronomy' for i in range(44, 55)},
                   }

def file_name_to_book(file_name):
    num_prefix = file_name[0:2]
    if not num_prefix.isdigit():
        return None
    num = int(num_prefix)
    if num == 0 or num > 54:
        return None
    return num_to_book_map[num]
if __name__ == "__main__":
    # chumash_base_dict = {}
    # for chumash in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    #     seg_refs = library.get_index(chumash).all_segment_refs()
    #     for seg_ref in seg_refs:
    #         chumash_base_dict[seg_ref.tref] = ""  # Initialize with empty string
    # # print(chumash_base_dict)

    directory = '../kehot_chp_chumash/html'
    for filename in sorted(os.listdir(directory)):
        file_path = os.path.join(directory, filename)
        if not os.path.isfile(file_path):
            continue
        print(file_path)
        current_book = file_name_to_book(filename)
        if current_book is None:
            continue
        # print(current_book)
        current_chapter = 0

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            html_content = file.read()
            # print(html_content)
        soup = BeautifulSoup(html_content, 'html.parser')
        target_classes = {"Peshat", "Peshat-Chapter-number-drop"}
        matches = soup.find_all(lambda tag: target_classes & set(tag.get("class", [])))
        for elem in matches:
            if "Peshat-Chapter-number-drop" in elem.attrs["class"]:
                current_chapter = int(elem.text.strip())
                print(current_chapter)
            # print(elem)