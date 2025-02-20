import django
import csv
import time

django.setup()

from sefaria.model import *


def retrieve_new_chapter_names():
    data = {}
    with open("perek_names - final.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            key = f"{row['Masekhet']} {row['#']}"
            data[key] = row['English']
    return data

def retrieve_babylonian_talmud_masechtot():
    return library.get_indexes_in_corpus('Bavli')

def name_changer(masechet_index, new_names_data):
    """
    This function iterates through the alt structure nodes for a given Masechet and renames
    the title, then saves the Index.
    :param masechet_index: The Index object for the given Masechet
    :param new_names_data: The data dict for the new names, where the key is the masechet name and chapter number
    and the value is the updated name for that chapter.
    :return: None
    """
    chap_num = 0
    for node in masechet_index.alt_structs['Chapters']['nodes']:

        chap_num += 1

        new_title = new_names_data[f"{masechet} {chap_num}"]

        print(f">> Updating {masechet} {chap_num} to {new_title}")

        chapter_title_list = node["titles"]
        for title in chapter_title_list:
            if title['lang'] == 'en':
                title['text'] = new_title

    masechet_index.save()

def test_title_changed(new_names_data, masechet):
    masechet_index = Ref(masechet).index

    chap_num = 0
    for node in masechet_index.alt_structs['Chapters']['nodes']:

        chap_num += 1

        new_title = new_names_data[f"{masechet} {chap_num}"]

        chapter_title_list = node["titles"]
        for title in chapter_title_list:
            if title['lang'] == 'en':
                assert title['text'] == new_title


def test_all_titles_changed():
    new_names_data = retrieve_new_chapter_names()
    masechtot = retrieve_babylonian_talmud_masechtot()
    for masechet in masechtot:
        test_title_changed(new_names_data, masechet)

def test_bava_kamma_hebrew():
    bk_index = Ref("Bava Kamma 2").index
    assert bk_index.alt_structs["Chapters"]["nodes"][1]["titles"][1]["text"] == "כיצד הרגל"


if __name__ == '__main__':

    start = time.time()

    # Ingest CSV
    new_names_data = retrieve_new_chapter_names()

    # Retrieve all masechtot
    masechtot = retrieve_babylonian_talmud_masechtot()

    # Run the name-changer on a masechet-by-masechet basis
    for masechet in masechtot:
       masechet_index = Ref(masechet).index
       print(masechet_index)
       name_changer(masechet_index, new_names_data)

    end = time.time()

    print(f"Total run time {end-start}")

    # Hebrew fix
    bk_index = Ref("Bava Kamma 2").index
    bk_index.alt_structs["Chapters"]["nodes"][1]["titles"][1]["text"] = "כיצד הרגל"
    bk_index.save()

