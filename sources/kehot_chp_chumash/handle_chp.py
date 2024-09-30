import django

django.setup()
from sefaria.model import *
from sefaria.tracker import modify_bulk_text
import os
from bs4 import BeautifulSoup
import re
import csv
superuser_id = 171118


def content_fixes(html_content):
    html_content = html_content.replace("Rashi on Leviticus 24:1", "Rashi on Leviticus 24:2")
    return html_content

def ingest_version(book, map_text):
    index = library.get_index(f"{book}")
    cur_version = VersionSet({'title': f'{book}', 'versionTitle': "The Torah; Chabad House Publications, Los Angeles, 2015-2023"})
    if cur_version.count() > 0:
        cur_version.delete()
        print("deleted existing version")
    chapter = index.nodes.create_skeleton()
    version = Version({"versionTitle": "The Torah; Chabad House Publications, Los Angeles, 2015-2023",
                       "versionSource": "https://www.chabadhousepublications.org/books",
                       "title": f"{book}",
                       "language": "en",
                       "chapter": chapter,
                       "digitizedBySefaria": True,
                       "license": "PD",
                       "status": "locked"
                       })

    modify_bulk_text(superuser_id, version, map_text)


def partition_dict_by_first_word(d):
    partitioned_dicts = {}
    for key, value in d.items():
        first_word = key.split()[0]
        if first_word not in partitioned_dicts:
            partitioned_dicts[first_word] = {}
        partitioned_dicts[first_word][key] = value
    return partitioned_dicts

def extract_elements_with_class(html_content, *class_names):
    soup = BeautifulSoup(html_content, 'html.parser')
    elements = soup.find_all(class_=list(class_names))
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


def replace_bold_and_italic_span(text):
    # pattern = r'<span class="bold">\s*(.*?)\s*</span>'

    small_patterns = [r'<span class="bold CharOverride-6">(.*?)</span>',
                      r'<span class="bold CharOverride-5">(.*?)</span>',
                      r'<span class="bold CharOverride-2">(.*?)</span>',
                      r'<span class="bold CharOverride-3">(.*?)</span>',
                      r'<span class="bold CharOverride-4">(.*?)</span>',
                      r'<span class="bold CharOverride-8">(.*?)</span>',
                      ]
    bold_patterns = [r'<span class="bold">(.*?)</span>',
                r'<span class="Peshat-PN">(.*?)</span>',
                r'<span class="bd">(.*?)</span>']
    italic_patterns = [r'<span class="italic">(.*?)</span>',]
    def replace_bold(match):
        content = match.group(1)
        return f'${content}#'
    def replace_italic(match):
        content = match.group(1)
        return f'@@@{content}/@@@'
    def replace_small(match):
        content = match.group(1)
        return f'$SMALL&BOLD{content}/$SMALL&BOLD'
    for pattern in bold_patterns:
        text = re.sub(pattern, replace_bold, text)
    for pattern in italic_patterns:
        text = re.sub(pattern, replace_italic, text)
    for pattern in small_patterns:
        text = re.sub(pattern, replace_small, text)
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
        if not text:
            return False
        return text[0].isdigit() and not text.startswith("603,550") and not text.startswith("301,775")

    verse_text = verse_text.replace('$', '')
    verse_text = verse_text.replace('#', '')
    verse_text = re.sub(r"FOOTNOTE_MARK(.*?)/FOOTNOTE_MARK", "", verse_text)
    verse_text = re.sub(r"FOOTNOTE(.*?)/FOOTNOTE", "", verse_text )
    address = extract_number_pair(verse_text)
    if address:
        c_num, v_num = address
        current_chapter_num = c_num
        current_verse_num = v_num
        return c_num, v_num
    if not begins_with_number(verse_text):
        return current_chapter_num, current_verse_num
    if extract_first_number(verse_text):
        first_num = int(extract_first_number(verse_text))
        if first_num == current_chapter_num:
            return current_chapter_num, current_verse_num
        v_num = first_num
        current_verse_num = v_num
        return current_chapter_num, v_num
    else:
        current_verse_num += 1
        return current_chapter_num, current_verse_num

def contains_english_letters(text):
    return bool(re.search(r'[a-zA-Z]', text))

def replace_symbols_with_bold_tags(text):
    text = text.replace('$', '<b>').replace('#', '</b>')
    return text


def find_and_remove_b_num_b(s: str, n: int):
    # Regex pattern to match <b>NUMBER</b> where NUMBER can be digits and spaces
    pattern = r'<b>\s*\d+\s*</b>'
    match = re.search(pattern, s)
    if not match:
        return s
    if match.start() > n:
        return s
    return s[match.end():]

def format_text_map(text_map):
    for key in text_map:
        text = text_map[key]
        text = text.replace('/$SMALL&BOLD', '</b></small>')
        text = text.replace('$SMALL&BOLD', '<b><small>')
        text = replace_symbols_with_bold_tags(text)
        text = find_and_remove_b_num_b(text, 40)
        match = re.search(r"<b>\d+", text)
        if match and match.start() < 40:
            text = "<b> "+ text[match.end():]
        text = text.replace('/@@@', "</i>")
        text = text.replace('@@@', "<i>")
        text = text.replace('/FOOTNOTE_MARKER', "</sup>")
        text = text.replace('FOOTNOTE_MARKER', '<sup class="footnote-marker">')
        text = text.replace('/FOOTNOTE', '</i>')
        text = text.replace('FOOTNOTE', '<i class="footnote">')
        text_map[key] = text
    return text_map

def clean_for_footnotes_extraction(html_content):
    def replace_italicized_footnote(match):
        content = match.group(1)
        return f'@@@{content}/@@@'
    html_content = html_content.replace('<span class="FNN-Peshat">&nbsp;</span>', ' ')
    html_content = html_content.replace('<span class="FNN-Peshat">&#160;</span>', ' ')
    html_content = re.sub('<span class="O-it-text-in-footnotes">(.*?)</span>', replace_italicized_footnote, html_content)
    html_content = re.sub('<span class="it-caption">(.*?)</span>', replace_italicized_footnote, html_content)
    # itcaption_pattern = r'<span class="it-caption">(.*?)</span>'
    # def replace_itcaption(match):
    #     content = match.group(1)
    #     return f'{content}'
    # html_content = re.sub(itcaption_pattern, replace_itcaption, html_content)
    return html_content

def extract_footnotes(html_content):
    html_content = clean_for_footnotes_extraction(html_content)
    soup = BeautifulSoup(html_content, 'html.parser')
    footnote_elements = soup.find_all('span', class_='FNN-Peshat')
    footnotes = {}
    for i, footnote_element in enumerate(footnote_elements):
        footnote_number = footnote_element.text.replace(".", "").strip()
        if footnote_number=='67':
            halt = True
        footnote_text = footnote_element.next_sibling
        footnote_texts = []
        while footnote_text and not (footnote_text.name == 'span' and 'FNN-Peshat' in footnote_text.get('class', [])):
            if isinstance(footnote_text, str):
                footnote_texts.append(footnote_text.strip())
            else:
                footnote_texts.append(footnote_text.text.strip())
            footnote_text = footnote_text.next_sibling
        footnote_text_combined = ' '.join(footnote_texts).strip()
        if footnote_text_combined and footnote_text_combined[0] == '.':
            footnote_text_combined = footnote_text_combined[1:].strip()
        footnotes[footnote_number] = footnote_text_combined
    return footnotes

def insert_footnotes(html_content, footnotes_map):
    soup = BeautifulSoup(html_content, 'html.parser')
    # Find all spans with the specific class and replace the text
    # for span in soup.find_all('span', class_='FNR-Peshat _idGenCharOverride-2'):
    for span in soup.find_all('span', class_='FNR-Peshat'):

        if span.text in footnotes_map:
            span.string = f'FOOTNOTE_MARKER{span.text}/FOOTNOTE_MARKER FOOTNOTE{footnotes_map[span.string]}/FOOTNOTE'
    modified_html = str(soup)
    return modified_html



if __name__ == '__main__':
    overrides = set()

    text_map = {}
    directory = 'html'
    for filename in sorted(os.listdir(directory)):
        file_path = os.path.join(directory, filename)
        if not os.path.isfile(file_path):
            continue
        print(file_path)
        current_book = file_name_to_book(filename)
        if current_book is None:
            continue
        print(current_book)

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            html_content = file.read()
            html_content = content_fixes(html_content)
            footnotes_map = extract_footnotes(html_content)
            html_content = insert_footnotes(html_content, footnotes_map)
            html_content = replace_bold_and_italic_span(html_content)
            # elements = extract_elements_with_class(html_content, 'Peshat', "Peshat-Heading")
            elements = extract_elements_with_class(html_content, 'Peshat')
            for element in elements:
                address = extract_verse_address(element.text)
                if "to affix the onyx stones to the upper ends of the Ephod’s shoulder straps," in element.text:
                    address = (12, 13)
                if not contains_english_letters(element.text):
                    continue
                ref = f"{current_book} {address[0]}:{address[1]}"
                if ref in text_map:
                    text_map[ref] += f" {element.text}"
                else:
                    text_map[ref] = element.text
                print(ref)
                print(element.text)
                print(text_map[ref])

                matches = re.findall(r'CharOverride-\d+', html_content)
                for match in matches:
                    overrides.add(match)


    print(overrides)
    text_map = format_text_map(text_map)
    with open('output.csv', mode='w', newline='') as file:
        csv.writer(file).writerows([['Ref', 'Text']] + list(text_map.items()))
    partitioned_map = partition_dict_by_first_word(text_map)
    for book, map in partitioned_map.items():
        ingest_version(book, map)
    print('hi')
