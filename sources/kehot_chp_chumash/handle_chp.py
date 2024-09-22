import django
django.setup()
from sefaria.model import *
import os
from bs4 import BeautifulSoup
import re


def extract_elements_with_class(html_content, class_name):
    soup = BeautifulSoup(html_content, 'html.parser')
    elements = soup.find_all(class_=class_name)
    return elements

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


def replace_bold_span(text):
    # pattern = r'<span class="bold">\s*(.*?)\s*</span>'
    patterns = [r'<span class="bold">(.*?)</span>',
                r'<span class="Peshat-PN">(.*?)</span>',
                r'<span class="bd">(.*?)</span>']
    def replace(match):
        content = match.group(1)
        return f'${content}#'
    for pattern in patterns:
        text = re.sub(pattern, replace, text)
    return text

current_chapter_num = None
current_verse_num = None
def extract_verse_address(verse_text):
    global current_chapter_num
    global current_verse_num
    def extract_number_pair(text):
        pattern = r'(\d+):(\d+)'
        match = re.search(pattern, text)
        if match:
            return int(match.group(1)), int(match.group(2))
        else:
            return None

    def extract_first_number(text):
        pattern = r'\d+'
        match = re.search(pattern, text)
        if match:
            return match.group(0)
        else:
            return None

    def begins_with_number(text):
        text = text.replace(' ', '').replace('$','').replace('#', "").strip()
        return text[0].isdigit()

    verse_text = verse_text.replace('$', '')
    verse_text = verse_text.replace('#', '')
    address = extract_number_pair(verse_text)
    if address:
        c_num, v_num = address
        current_chapter_num = c_num
        current_verse_num = v_num
        return c_num, v_num
    if not begins_with_number(verse_text):
        return current_chapter_num, current_verse_num
    if extract_first_number(verse_text):
        v_num = int(extract_first_number(verse_text))
        current_verse_num = v_num
        return current_chapter_num, v_num
    else:
        current_verse_num += 1
        return current_chapter_num, current_verse_num




if __name__ == '__main__':
    directory = 'html'
    for filename in sorted(os.listdir(directory)):
        file_path = os.path.join(directory, filename)
        if not os.path.isfile(file_path):
            continue
        print(file_path)
        current_book = file_name_to_book(filename)
        print(current_book)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            html_content = file.read()
            html_content = replace_bold_span(html_content)
            elements = extract_elements_with_class(html_content, 'Peshat')
            for element in elements:
                address = extract_verse_address(element.text)
                print(f"{current_book} {address[0]}:{address[1]}")
                print(element.text)
                # print(extract_verse_address(element.text))
