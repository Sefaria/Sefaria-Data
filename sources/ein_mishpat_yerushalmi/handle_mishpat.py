
import django

django.setup()
from tqdm import tqdm
superuser_id = 171118
import csv
import re
from sefaria.model import *
from sefaria.utils.talmud import daf_to_section, section_to_daf
from typing import List
from pprint import pprint
import copy
from bs4 import BeautifulSoup
from linking_utilities.dibur_hamatchil_matcher import match_text, match_ref


def html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    return soup.get_text()

def simple_tokenizer(text):
    """
    A simple tokenizer that splits text into tokens by whitespace,
    and removes apostrophes and periods from the tokens.
    """

    def remove_nikkud(hebrew_string):
        # Define a regular expression pattern for Hebrew vowel points
        nikkud_pattern = re.compile('[\u0591-\u05BD\u05BF-\u05C2\u05C4\u05C5\u05C7]')

        # Use the sub method to replace vowel points with an empty string
        cleaned_string = re.sub(nikkud_pattern, '', hebrew_string)

        return cleaned_string
    # Replace apostrophes and periods with empty strings
    text = text.replace("'", "")
    text = text.replace(".", "")
    text = text.replace("׳", "")
    text = text.replace("–", "")
    text = text.replace(";", "")
    text = remove_nikkud(text)

    # Split the text into tokens by whitespace
    tokens = text.split()
    return tokens

def remove_divs_starting_with_text(html_content, prefix):
    """
    Remove all <div> elements from the HTML content whose text starts with the specified prefix.

    Parameters:
    - html_content (str): The HTML content as a string.
    - prefix (str): The prefix to match at the beginning of the text.

    Returns:
    - str: The modified HTML content as a string.
    """

    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all <div> elements whose text starts with the prefix
    divs_to_remove = [div for div in soup.find_all('div') if div.get_text().strip().startswith(prefix)]

    # Remove the identified <div> elements
    for div in divs_to_remove:
        div.decompose()

    # Convert the BeautifulSoup object back to a string
    modified_html = str(soup)

    return modified_html

# def infer_links(ri_amud, talmud_amud):
#     from sources.functions import match_ref_interface
#     segs = Ref(ri_amud).all_segment_refs()
#     comments = [seg.text("he").text for seg in segs]
#     talmud_amud_extended = ""
#     try:
#         talmud_amud_extended = (Ref(talmud_amud).to(Ref(talmud_amud).all_segment_refs()[-1].next_segment_ref())).normal()
#     except:
#         talmud_amud_extended = talmud_amud
#     matches = match_ref_interface(talmud_amud_extended, ri_amud,
#                              comments, simple_tokenizer, dher)
#     return matches

def get_dh(text):
    result = re.sub(r'\$.+?\$', '', text)
    return result
def list_of_tuples_to_csv(data, filename='output.csv'):
    """
    Converts a list of tuples to a CSV file.

    Parameters:
    data (list of tuples): The data to write to the CSV file.
    filename (str): The name of the output CSV file.

    Returns:
    None
    """
    try:
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        print(f"Data has been written to {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")
def link_markers_to_sefaria_segments(comments_list):
    base_text = Ref('Jerusalem Talmud Pesachim').text('he')
    base_text_list = [seg.text('he') for seg in library.get_index('Jerusalem Talmud Pesachim').all_segment_refs()]
    links = match_ref(base_text_list, comments_list, simple_tokenizer, dh_extract_method=get_dh, chunks_list=True)
    table = []
    for marker, matched in zip(comments_list, links['matches']):
        tref = matched.tref if matched else ""
        url = "https://www.sefaria.org/"+matched.url() if matched else ""
        table.append( (marker, tref, url) )
    list_of_tuples_to_csv(table)
    print(links)


def extract_with_context(text, span, num_words_before, num_words_after):
    import re

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

if __name__ == '__main__':
    # Reading HTML content from a file
    with open('ביאור_ירושלמי מאיר_מסכת פסחים_פרק ראשון – ויקיטקסט.html', 'r', encoding='utf-8') as file:
        html_content = file.read()

    pattern = r'\b[\u0590-\u05FF]+_[\u0590-\u05FF]+\b'
    html_content = re.sub(pattern, lambda m: f"${m.group()}$", html_content)
    html_content = remove_divs_starting_with_text(html_content, 'עין משפט ונר מצוה')
    plain_text = html_to_text(html_content)
    # Using re.findall to find all matches
    matches = re.compile(r'\$.+?\$').finditer(plain_text)
    comments = []
    for match in matches:
        match_text = plain_text[match.regs[0][0]:match.regs[0][1]]
        if all(term not in match_text for term in ['מסכת', 'פרק', 'ירושלמי']):
            extraction = extract_with_context(plain_text, (match.regs[0][0], match.regs[0][1]), 1, 5)
            comments.append(extraction)

    for index, c in enumerate(comments):
        print(str(index) + ": " + c)
    link_markers_to_sefaria_segments(comments)
    print(plain_text)
    print("hello world")
