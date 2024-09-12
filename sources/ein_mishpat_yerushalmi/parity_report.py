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

def get_html_files(directory):
    html_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                html_files.append(os.path.join(root, file))

    html_files.sort(key=os.path.getctime)

    # Yield sorted files
    for file in html_files:
        yield file

def extract_first_number(string):
    match = re.search(r'\d+', string)
    return int(match.group()) if match else None

def infer_sefaria_segment_for_markers(html_content, masechet_name, chapter_num):
    pattern = r'\b[\u0590-\u05FF]+_[\u0590-\u05FF]+\b'
    html_content = re.sub(pattern, lambda m: f"${m.group()}$", html_content)
    html_content = remove_divs_starting_with_text(html_content, 'עין משפט ונר מצוה')
    html_content = remove_paragraphs_starting_with_text(html_content, "קישורים")
    html_content = remove_elements_by_tag(html_content, ['h3', 'figure'])
    plain_text = html_to_text(html_content)
    #remove
    #מפרשים:
    #   ^[דף ג עמוד ב]
    #from page
    plain_text = re.sub(r"מפרשים:\s*\^\[.*?\]", '', plain_text)
    # Using re.findall to find all matches
    matches = re.compile(r'\$.+?\$').finditer(plain_text)
    comments = []
    for match in matches:
        match_text = plain_text[match.regs[0][0]:match.regs[0][1]]
        if all(term not in match_text for term in ['מסכת', 'פרק', 'ירושלמי']):
            extraction = extract_with_context(plain_text, (match.regs[0][0], match.regs[0][1]), 0, 5)
            comments.append(extraction)

    for index, c in enumerate(comments):
        print(str(index) + ": " + c)
    link_markers_to_sefaria_segments(comments, masechet_name, chapter_num)

if __name__ == '__main__':
    for wikifile in get_html_files('wiki_data'):
        # print(wikifile)
        with open(wikifile, 'r', encoding='utf-8') as file:
            html_content = file.read()
            infer_footnotes_links(html_content, filename=str(wikifile))
    # simple_validation()