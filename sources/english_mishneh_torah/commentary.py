# Strategy
# Iterate through the files, scraping commentary where present.
# Per line of commentary, create a CSV with the following fields:
#  CSV:  ref, dibur hamatchil, commentary
# Use the CSV to insert commentary as footnotes for each halacha,
# renumber footnotes for the chapter accordingly.
from bs4 import BeautifulSoup
import re
import csv
import os
from utilities import number_map, chabad_book_names, sefaria_book_names, create_book_name_map

book_name_map = create_book_name_map(chabad_book_names, sefaria_book_names)


def get_commentary(file):
    soup = BeautifulSoup(file, 'html.parser')
    capture = soup.find_all(class_="co_commentary")
    return capture


def get_ref_metadata(file):
    soup = BeautifulSoup(file, 'html.parser')
    capture = soup.find_all(class_="rambam_h2")[0]
    capture = str(capture)
    return capture


def get_chapter(file):
    capture = get_ref_metadata(file)
    regex_tuple = re.findall(r">(.*) - (.*)<", capture)[0]
    en_chapter = regex_tuple[1]
    # NOTE: Skipping Haggadah text for now
    if en_chapter == "Text of the Haggadah":
        pass
    num_chapter = number_map[en_chapter]
    return num_chapter


def get_book(file):
    capture = get_ref_metadata(file)
    regex_tuple = re.findall(r">(.*) - (.*)<", capture)[0]
    book = regex_tuple[0]
    sef_book = book_name_map[book]
    return sef_book


def get_halakha_number(file):
    number = re.findall(r"<co:rambam_commentary halacha=\"(\d*?)\">", file)
    return number[0]


def make_ref(book, chapter, halakha):
    return f"{book} {chapter}.{halakha}"

def extract_dibbur_hamatchil(txt):
    #Note: some have one ending hyphen, some have two
    dhm = re.findall(r"^(.*?) -</b>", txt)
    if not dhm:
        dhm = re.findall(r"^(.*?) --</b>", txt)
    return dhm

def extract_commentary_body(txt):
    comm = re.findall(r"</b>(.*?)</p>", txt)
    if not comm:
        print(txt)
    return comm


html_dir = './html'
count = 0
for chapter_file in os.listdir(html_dir):
    f = os.path.join(html_dir, chapter_file)
    if os.path.isfile(f):
        with open(f, 'r') as file:
            cur_file = file.read()
            commentary = get_commentary(cur_file)
            if commentary:
                chapter = get_chapter(cur_file)
                book = get_book(cur_file)
                for com in commentary:
                    str_com = str(com)
                    num = get_halakha_number(str_com)
                    ref = make_ref(book, chapter, num)
                    comm_list = re.findall(r"<p><b>(.*?)<p><b>", str_com, re.DOTALL)
                    for comment in comm_list:
                        # print(comment)
                        # print("")
                        dhm = extract_dibbur_hamatchil(comment)
                        commentary_body = extract_commentary_body(comment)
                        # print(f"{ref}, {dhm}, {commentary_body}")
