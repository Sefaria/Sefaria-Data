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

def remove_divs_starting_with_text(html_content, prefix):
    soup = BeautifulSoup(html_content, 'html.parser')
    divs_to_remove = [div for div in soup.find_all('div') if div.get_text().strip().startswith(prefix)]
    for div in divs_to_remove:
        div.decompose()

    modified_html = str(soup)
    return modified_html

def remove_paragraphs_starting_with_text(html_content, prefix):
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs_to_remove = [p for p in soup.find_all('p') if p.get_text().strip().startswith(prefix)]
    for p in paragraphs_to_remove:
        p.decompose()

    modified_html = str(soup)

    return modified_html

def remove_elements_by_tag(html_content, tag_names: List):
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag_name in tag_names:
        for element in soup.find_all(tag_name):
            element.decompose()
    return str(soup)

def html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    return soup.get_text()

def extract_with_context(text, span, num_words_before, num_words_after):
    # Define a regex pattern that includes words and words surrounded by dollar signs
    pattern = r'\$?\b\w+\b\$?'

    # Extracting the span text
    span_text = text[span[0]:span[1]]

    # Finding the start index of the span in terms of word positions
    words = re.findall(pattern, text)
    start_idx = len(re.findall(pattern, text[:span[0]]))

    # Getting the indices of the context words
    start_context = max(0, start_idx - num_words_before)
    end_context = min(len(words), start_idx + num_words_after + len(re.findall(pattern, span_text)))

    # Extracting the relevant words
    context_words = words[start_context:end_context]

    # Join the context words to form the result
    result = ' '.join(context_words)

    return result

def get_inline_footnotes(html_content):
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
            extraction = extract_with_context(plain_text, (match.regs[0][0], match.regs[0][1]), 1, 5)
            comments.append(extraction)

    # for index, c in enumerate(comments):
    #     print(str(index) + ": " + c)
    return comments

def get_divs_starting_with_text(html_content, prefix):
    soup = BeautifulSoup(html_content, 'html.parser')
    divs_to_get = [div.get_text().strip() for div in soup.find_all('div') if div.get_text().strip().startswith(prefix)]
    return divs_to_get

def get_bottom_footnotes(html_content):
    divs_text = get_divs_starting_with_text(html_content, 'עין משפט ונר מצוה')
    footnotes_lines = []
    for div_text in divs_text:
        lines = concatenate_lines(div_text)
        lines_starting_with_number = [
            line for line in lines if line.lstrip() and line.lstrip().split() and line.lstrip().split()[0][0].isdigit()
        ]
        # footnotes_lines += lines_starting_with_number
        formatted_lines = []
        for line in lines_starting_with_number:
            match = re.search(r'[\u0590-\u05FF]+_[\u0590-\u05FF]+\b', line)
            if match:
                matched_text = match.group(0)
                # Insert $ signs and replace the original match in the string
                updated_line = re.sub(r'[\u0590-\u05FF]+_[\u0590-\u05FF]+\b', f"${matched_text}$", line)
                formatted_lines += [updated_line]
        footnotes_lines += formatted_lines

    return footnotes_lines

def extract_text_within_dollars(string):
    # Use regular expression to find text within $...$
    match = re.search(r'\$(.*?)\$', string)
    if match:
        return match.group(1).replace(" ", "")  # Return the text between $ signs
    return None

if __name__ == '__main__':
    report_data = []
    for wikifile in get_html_files('wiki_data'):
        print(wikifile)
        with open(wikifile, 'r', encoding='utf-8') as file:
            html_content = file.read()
            # infer_footnotes_links(html_content, filename=str(wikifile))
        inline = get_inline_footnotes(html_content)
        bottom = get_bottom_footnotes(html_content)
        for inline_footnote in inline:
            inline_marker = extract_text_within_dollars(inline_footnote)
            # if not inline_marker:
            #     print("\tMissing Inline Marker:", inline_footnote)
            #     continue
            bottom_matches = [bottom_footnote for bottom_footnote in bottom if inline_marker in bottom_footnote]
            if not bottom_matches:
                print("\tInline Marker without Bottom Marker:", inline_footnote)
                report_data.append({
                    "filename": wikifile,
                    "Marker": inline_marker,
                    "Type of Error": "Inline Marker without Bottom Marker"
                })
        for bottom_footnote in bottom:
            bottom_marker = extract_text_within_dollars(bottom_footnote)
            # if not bottom_marker:
            #     print("\tMissing Bottom Marker:", bottom_footnote)
            #     continue
            inline_matches = [inline_footnote for inline_footnote in inline if bottom_marker in inline_footnote]
            if not inline_matches:
                print("\tBottom Marker without Inline Marker:", bottom_footnote)
                report_data.append({
                    "filename": wikifile,
                    "Marker": bottom_marker,
                    "Type of Error": "Bottom Marker without Inline Marker"
                })
    # Write to CSV file
    with open('output.csv', mode='w', newline='') as file:
        fieldnames = report_data[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_data)
