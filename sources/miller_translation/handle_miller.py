import django

django.setup()

superuser_id = 171118
import csv
from sefaria.model import *
import re
from sefaria.tracker import modify_bulk_text
from bs4 import BeautifulSoup

new_verse_token = "$DIGIT_NEW_VERSE: "
new_chapter_token = "$DIGIT_NEW_CHAPTER: "
header_token = "$HEADER: "
comment_token = "$COMMENT: "
def get_list_of_verses(html_document):
    soup = BeautifulSoup(html_document, 'html.parser')
    soup = prepend_to_text_in_elements(soup, "TRANSLATION-SMALL-HEADINGS", comment_token)
    soup = prepend_to_text_in_elements(soup, "TRANSLATION-HEADINGS", header_token)
    soup = prepend_to_text_in_elements(soup, "CharOverride-3", new_verse_token)
    soup = prepend_to_text_in_elements(soup, "CharOverride-2", new_chapter_token)
    soup = prepend_to_text_in_elements(soup, "CharOverride-16", new_chapter_token)
    selected_elements = soup.find_all(class_=lambda x: x and (x.startswith("ParaOverride-") or x.startswith("TRANSLATION-HEADINGS")))
    text_list = [clean_line(element.text) for element in selected_elements]
    clean_text = ''.join(text_list)
    text_list = clean_text.split("$")
    return text_list

def clean_line(line):
    line = replace_double_digits(line, new_verse_token)
    line = replace_double_digits(line, new_chapter_token)
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
        if element.string:
            element.string.replace_with(prepended_text + element.get_text())

    return soup

def count_elements_with_class(html_document, class_name):
    soup = BeautifulSoup(html_document, 'html.parser')
    selected_elements = soup.find_all(class_=class_name)

    return len(selected_elements)
if __name__ == '__main__':
    print("hello world")
    html_document = open("data/01 SEFER BREISHIS ABRIDGED FINAL square boxes.html", 'r', encoding='utf-8').read()
    para = get_list_of_verses(html_document)
    print(f"comments in Genesis count: {count_elements_with_class(html_document, 'TRANSLATION-SMALL-HEADINGS')}")



    print("end")



