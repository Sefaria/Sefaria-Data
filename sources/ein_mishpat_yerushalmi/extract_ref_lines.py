import django

django.setup()
from tqdm import tqdm
import os
superuser_id = 171118
import csv
import re
from sefaria.model import *
from sefaria.utils.talmud import daf_to_section, section_to_daf
from typing import List
from pprint import pprint
import copy
from bs4 import BeautifulSoup

def get_divs_starting_with_text(html_content, prefix):
    soup = BeautifulSoup(html_content, 'html.parser')
    divs_to_get = [div.get_text().strip() for div in soup.find_all('div') if div.get_text().strip().startswith(prefix)]
    return divs_to_get

def concatenate_lines(input_string):
    lines = input_string.splitlines()
    result = []

    for line in lines:
        stripped_line = line.strip()
        if stripped_line and stripped_line[0].isdigit():
            result.append(line)
        else:
            if result:
                result[-1] += ' ' + line.strip()
            else:
                result.append(line)

    return result
def infer_footnotes_links(html_content, filename=""):
    divs_text = get_divs_starting_with_text(html_content, 'עין משפט ונר מצוה')
    markers_footnotes = []
    # linker = library.get_linker("he")
    for div_text in divs_text:
        lines = concatenate_lines(div_text)
        lines_starting_with_number = [
            line for line in lines if line.lstrip() and line.lstrip().split() and line.lstrip().split()[0][0].isdigit()
        ]
        for line in lines_starting_with_number:
            match = re.search(r'[\u0590-\u05FF]+_[\u0590-\u05FF]+\b', line)
            marker = match.group() if match else None
            if match:
                print(match.string)
                # print(filename)
def get_html_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                yield os.path.join(root, file)
def extract_first_number(string):
    match = re.search(r'\d+', string)
    return int(match.group()) if match else None
def simple_validation():
    for wikifile in get_html_files('wiki_data'):
        # print(wikifile)
        move_to_next_chapter = False
        comments_index_for_perek = 0
        with open(wikifile, 'r', encoding='utf-8') as file:
            html_content = file.read()
        divs_text = get_divs_starting_with_text(html_content, 'עין משפט ונר מצוה')
        markers_footnotes = []
        for div_text in divs_text:
            lines = concatenate_lines(div_text)
            lines_starting_with_number = [
                line for line in lines if
                line.lstrip() and line.lstrip().split() and line.lstrip().split()[0][0].isdigit()
            ]
            for line in lines_starting_with_number:
                comments_index_for_perek += 1
                match = re.search(r'[\u0590-\u05FF]+_[\u0590-\u05FF]+\b', line)
                if not match:
                    continue
                marker = match.group() if match else None
                serial_number = extract_first_number(match.string)
                if serial_number != comments_index_for_perek:
                    print(wikifile)
                    print(f"{match.string}")
                    move_to_next_chapter = True
                    break
            if move_to_next_chapter:
                break


if __name__ == '__main__':
    for wikifile in get_html_files('wiki_data'):
        # print(wikifile)
        with open(wikifile, 'r', encoding='utf-8') as file:
            html_content = file.read()
            infer_footnotes_links(html_content, filename=str(wikifile))
    # simple_validation()
