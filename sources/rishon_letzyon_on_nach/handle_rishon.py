import django

django.setup()

superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
from sefaria.helper.schema import insert_last_child, reorder_children
from sefaria.tracker import modify_bulk_text
from sefaria.helper.category import create_category
from sefaria.system.database import db
# from bs4 import BeautifulSoup
# import os
import re
from typing import List

def compute_gematria(word):
    # Define the numerical values of each letter
    gematria = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}

    # Compute the Gematria of the word
    total = 0
    for letter in word:
        if letter in gematria:
            total += gematria[letter]

    return total


def hebrew_book_to_english(bookname):
    hebrew_to_english_map = {
        "בראשית": "Genesis",
        "שמות": "Exodus",
        "ויקרא": "Leviticus",
        "במדבר": "Numbers",
        "דברים": "Deuteronomy",
        "יהושע": "Joshua",
        "שופטים": "Judges",
        "שמואל א": "1 Samuel",
        "שמואל ב": "2 Samuel",
        "מלכים א": "1 Kings",
        "מלכים ב": "2 Kings",
        "ישעיהו": "Isaiah",
        "ירמיהו": "Jeremiah",
        "יחזקאל": "Ezekiel",
        "הושע": "Hosea",
        "יואל": "Joel",
        "עמוס": "Amos",
        "עבדיה": "Obadiah",
        "יונה": "Jonah",
        "מיכה": "Micah",
        "נחום": "Nahum",
        "חבקוק": "Habakkuk",
        "צפניה": "Zephaniah",
        "חגי": "Haggai",
        "זכריה": "Zechariah",
        "מלאכי": "Malachi",
        "תהילים": "Psalms",
        "איוב": "Job",
        "משלי": "Proverbs",
        "רות": "Ruth",
        "שיר השירים": "Song of Songs",
        "קהלת": "Ecclesiastes",
        "איכה": "Lamentations",
        "אסתר": "Esther",
        "דניאל": "Daniel",
        "עזרא": "Ezra",
        "נחמיה": "Nehemiah",
        "דברי הימים א": "1 Chronicles",
        "דברי הימים ב": "2 Chronicles",
    }

    return hebrew_to_english_map[bookname]



def ingest_mikra(parsed_books):
    for book in parsed_books:
        book_name = next(iter(book)).split()[0]
        if book_name == "Song":
            book_name = "Song of Songs"
        print("ingesting the book of " + book_name)
        index = library.get_index(book_name)
        cur_version = VersionSet({'title': book_name,
                                  "versionTitle" : "Miqra Mevoar, trans. and edited by David Kokhav, Jerusalem 2020"})

        if cur_version.count() > 0:
            cur_version.delete()
            print("deleted existing version")
        chapter = index.nodes.create_skeleton()
        version = Version({"versionTitle": "Miqra Mevoar, trans. and edited by David Kokhav, Jerusalem 2020",
                           "versionSource": "https://he.wikisource.org/wiki/%D7%9E%D7%A7%D7%A8%D7%90_%D7%9E%D7%91%D7%95%D7%90%D7%A8",
                           "title": book_name,
                           "language": "he",
                           "chapter": chapter,
                           "digitizedBySefaria": True,
                           "license": "PD",
                           "status": "locked"
                           })
        modify_bulk_text(superuser_id, version, book)
def read_csv_to_list_of_dicts(file_path):
    data = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(dict(row))
    return data

def fill_in_chapters_and_books(rishon_list: List[Dictionary]):
    prev = rishon_list[0]
    for dict in rishon_list[1:]:
        for key in dict:
            if dict[key] == '':
                dict[key] = prev[key]
        prev = dict
def fill_in_segment_nums(rishon_list: List[Dictionary]):
    prev = rishon_list[0]
    counter = 1
    prev["segment"] = counter
    for dict in rishon_list[1:]:
        if dict["book"] == prev["book"] and dict["chapter"] == prev["chapter"] and dict["verse"] == prev["verse"]:
            counter += 1
        else:
            counter = 1
        dict["segment"] = counter
        prev = dict
def fill_in_refs(rishon_list):
    prefix = "Rishon LeTzion on"
    for dict in rishon_list:
        tref = prefix + " " + hebrew_book_to_english(dict['book']) + " " + str(compute_gematria(dict["chapter"])) + ":" + str(compute_gematria(dict["verse"]))
        dict["ref"] = tref

def partition_dicts_by_key(dicts, key):
    partitions = {}
    for d in dicts:
        value = d.get(key)
        if value not in partitions:
            partitions[value] = []
        partitions[value].append(d)
    return partitions

if __name__ == '__main__':
    # validate()
    print("hi")
    rishon_list = read_csv_to_list_of_dicts("Rishon_LeTzion.csv")
    fill_in_chapters_and_books(rishon_list)
    fill_in_segment_nums(rishon_list)
    fill_in_refs(rishon_list)
    partitioned_by_books = partition_dicts_by_key(rishon_list, "book")
    print(partitioned_by_books)


    print("end")











