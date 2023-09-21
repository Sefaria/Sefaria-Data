import django

django.setup()

django.setup()
superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
from sefaria.helper.schema import insert_last_child, reorder_children
from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
from sefaria.helper.category import create_category
from sefaria.system.database import db
from bs4 import BeautifulSoup
import os


# import time

def post_indices():
    from sources.functions import post_index, add_term
    add_term("Targum Sheni", "תרגום שני", server="https://new-shmuel.cauldron.sefaria.org")
    # add_term("Targum Sheni", "תרגום שני")
    # add_term("Targum Sheni", "תרגום שני", server="https://new-shmuel.cauldron.sefaria.org")
    # index = post_index({'title': 'Targum_Sheni_on_Esther'}, server="https://new-shmuel.cauldron.sefaria.org", method="GET")
    # index["dependence"] = "targum"
    # index["base_text_titles"] = ["Esther"]
    # index["collective_titpsqlle"] = "Targum Sheni"
    # post_index(index, server="https://new-shmuel.cauldron.sefaria.org")

def get_mikra_refs(soup_object):
    matching_elements = soup_object.find_all(class_="mw-redirect")
    matching_elements = [element for element in matching_elements if element.get_text() != "הגרסה היציבה" and not "פרשת" in element.get_text()]
    matching_elements = [Ref(element.get("title")).normal() for element in matching_elements]
    return matching_elements

def get_mikra_text_and_bold_titles(soup_object):
    # Create an empty list to store matching elements
    matching_elements = []

    # Iterate through the document to find matching elements
    for element in soup.descendants:
        if element.name and element.get("style", "").strip() == "background:Gainsboro":
            matching_elements.append(element)
        elif element.name == "b":
            matching_elements.extend(element.find_all())

    not_a_title = {'', "פ", "ס", "^", "פ (בספרי תימן)", "פ (בספרי ספרד ואשכנז)", "כאן"}
    matching_elements2 = []
    for element in matching_elements:
        text = element.get_text()
        if not (text.strip() in not_a_title or "דף השיחה" in text):
            matching_elements2.append(element)

    final_strings = []
    if matching_elements2[0].name != "span":
        final_strings.append(matching_elements2[0].text)
    for previous, current in zip(matching_elements2, matching_elements2[1:]):
        if previous.name == 'span':
            element_string = '<b>' + previous.text + '</b>' + '<br>' + current.text
            final_strings.append(element_string)
        else:
            if current.name != "span":
                final_strings.append(current.text)



    return final_strings

def partition_dictionary(input_dict):
    result_list = []
    temp_dict = {}

    for key, value in input_dict.items():
        # Get the key prefix (the word before the first underscore)
        key_prefix = key.split(' ')[0]

        if key_prefix not in temp_dict:
            # Create a new dictionary for this key prefix
            temp_dict[key_prefix] = {}

        # Add the key-value pair to the corresponding dictionary
        temp_dict[key_prefix][key] = value

    # Convert the temporary dictionaries to a list
    result_list.extend(temp_dict.values())

    return result_list

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

if __name__ == '__main__':
    print("hello world")
    # List all files in the folder
    folder_path = "htmls"
    html_files = [f for f in os.listdir(folder_path) if f.endswith(".html")]
    parsed_books = []
    ref_and_text_dict = {}

    # Loop through each HTML file and process it
    for filename in html_files:
        file_path = os.path.join(folder_path, filename)

        with open(file_path, 'r', encoding='utf-8') as file:
            # Read the HTML content
            html_content = file.read()

        soup = BeautifulSoup(html_content, 'html.parser')


        mikra_refs = get_mikra_refs(soup)
        mikra_text = get_mikra_text_and_bold_titles(soup)



        for tref, text in zip(mikra_refs, mikra_text):
            ref_and_text_dict[tref] = text
        if len(mikra_refs) != len(mikra_text):
            print("discrepancy")
        # parsed_books.append(ref_and_text_dict)

    parsed_books = partition_dictionary(ref_and_text_dict)
    ingest_mikra(parsed_books)


    print("end")











