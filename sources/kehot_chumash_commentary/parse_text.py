
import django
django.setup()
from sefaria.model import *
from sources.functions import *
from bs4 import BeautifulSoup
import pandas as pd


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
def insert_style(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')

    for span in soup.find_all('span', class_='bold-small-text'):
        b_tag = soup.new_tag('b')
        b_tag.string = span.get_text()
        span.replace_with(b_tag)
    return str(soup)

if __name__ == "__main__":
    # chumash_base_dict = {}
    # for chumash in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    #     seg_refs = library.get_index(chumash).all_segment_refs()
    #     for seg_ref in seg_refs:
    #         chumash_base_dict[seg_ref.tref] = ""  # Initialize with empty string
    # # print(chumash_base_dict)
    book_map = {}

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
        curr_chapter_and_verse_num = None
        curr_segment_num = 0

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            html_content = file.read()
            # print(html_content)
        soup = BeautifulSoup(html_content, 'html.parser')
        # target_classes = {"Peshat", "Peshat-Chapter-number-drop"}
        # matches = soup.find_all(lambda tag: target_classes & set(tag.get("class", [])))
        chasidic_boxes = soup.find_all(class_="chasidic-insights-box")
        chasidic_ps = [p for box in chasidic_boxes for p in box.find_all("p")]
        for elem in chasidic_ps:
            match = re.match(r'^(\d+):(\d+)', elem.text.strip())
            chapter_and_verse_num = match.group(0) if match else None
            if chapter_and_verse_num:
                curr_chapter_and_verse_num = chapter_and_verse_num
                curr_segment_num = 0
            # print(elem.text.strip())
            if 'class="bold-small-text' in str(elem):
                curr_segment_num += 1
            key = f"{title} {current_book} {curr_chapter_and_verse_num}:{curr_segment_num}"
            book_map[key] = f"{book_map[key]}<br>{elem}" if key in book_map else str(elem)
    for key, value in book_map.items():
        book_map[key] = insert_style(value)
    pd.DataFrame(list(book_map.items()), columns=["ref", "html"]) \
        .to_html("book_map.html",  # output file
                 index=False,  # no row numbers
                 escape=False)  # keep the inner HTML un-escaped
    print('hi')