import django

django.setup()
from sefaria.model import *
from sefaria.tracker import modify_bulk_text
import os
from bs4 import BeautifulSoup
import re
import csv
superuser_id = 171118

char_overrides = {'CharOverride-1', 'CharOverride-10', 'CharOverride-11', 'CharOverride-12', 'CharOverride-2', 'CharOverride-3', 'CharOverride-4', 'CharOverride-5', 'CharOverride-6', 'CharOverride-7', 'CharOverride-8', 'CharOverride-9'}
num_to_book_map = {
    **{i: 'Genesis' for i in range(1, 13)},
    **{i: 'Exodus' for i in range(13, 24)},
    **{i: 'Leviticus' for i in range(24, 34)},
    **{i: 'Numbers' for i in range(34, 44)},
    **{i: 'Deuteronomy' for i in range(44, 55)},}
def extract_elements_with_class(html_content, *class_names):
    soup = BeautifulSoup(html_content, 'html.parser')
    elements = soup.find_all(class_=list(class_names))
    return elements
def file_name_to_book(file_name):
    num_prefix = file_name[0:2]
    if not num_prefix.isdigit():
        return None
    num = int(num_prefix)
    if num == 0 or num > 54:
        return None
    return num_to_book_map[num]

if __name__ == '__main__':
    directory = 'html'
    for filename in sorted(os.listdir(directory)):
        file_path = os.path.join(directory, filename)
        if not os.path.isfile(file_path):
            continue
        current_book = file_name_to_book(filename)
        if current_book is None:
            continue
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            html_content = file.read()

            elements = extract_elements_with_class(html_content, char_overrides)
            for element in elements:
                # print(filename)
                print(element)

