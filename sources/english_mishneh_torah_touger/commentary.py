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
from mt_utilities import number_map, chabad_book_names, sefaria_book_names, create_book_name_map

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
    if en_chapter == "Text of the Haggadah":
        num_chapter = 1
    else:
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
    dhm = re.findall(r"^(.*?)</b>", txt, re.DOTALL)
    return dhm[0]


def extract_commentary_body(txt):
    index_start = txt.find('</b>')
    index_start = index_start + len('</b>')
    comm_text = txt[index_start:]
    end_scrape = comm_text.find('</co:rambam_commentary>')
    if end_scrape > 0:
        return comm_text[:end_scrape]
    return txt[index_start:]


def scrape_commentary():
    html_dir = './html'
    footnote_dict_list = []
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
                        print(f"Scraping commentary for {ref}")
                        comm_list = re.split(r"<b>", str_com, re.DOTALL)
                        comm_list = comm_list[1:]
                        footnote_dict_list.append(
                            {'ref': ref, 'commentary': comm_list})
    return footnote_dict_list


def export_cleaned_data_to_csv(list):
    """
    This function writes the data to a new CSV
    """
    with open('commentary.csv', 'w+') as csvfile:
        headers = ['ref', 'commentary']
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writerows(list)


if __name__ == '__main__':
    commentary_list = scrape_commentary()
    export_cleaned_data_to_csv(commentary_list)
