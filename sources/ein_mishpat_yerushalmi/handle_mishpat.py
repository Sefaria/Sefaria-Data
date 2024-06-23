
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


def html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    return soup.get_text()


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



if __name__ == '__main__':
    # Reading HTML content from a file
    with open('ביאור_ירושלמי מאיר_מסכת פסחים_פרק ראשון – ויקיטקסט.html', 'r', encoding='utf-8') as file:
        html_content = file.read()

    pattern = r'\b[\u0590-\u05FF]+_[\u0590-\u05FF]+\b'
    html_content = re.sub(pattern, lambda m: f"${m.group()}$", html_content)
    html_content = remove_divs_starting_with_text(html_content, 'עין משפט ונר מצוה')
    plain_text = html_to_text(html_content)
    print(plain_text)
    print("hello world")
