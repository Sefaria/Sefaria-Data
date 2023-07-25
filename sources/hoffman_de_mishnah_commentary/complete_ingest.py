import django

django.setup()

import time
from collections import defaultdict
from sefaria.model import *
from sefaria.tracker import modify_bulk_text
from sources.functions import post_text, post_link
from sources.local_settings import SEFARIA_SERVER
from sources.hoffman_de_mishnah_commentary.extract_commentary import create_text_data_dict
from sources.hoffman_de_mishnah_commentary.parse_intro_xml import process_xml
from sources.hoffman_de_mishnah_commentary.create_index import create_index_main, create_term_and_category

# TODO: General
# - fix categories so not all under one heading
# - Work on validations

def create_mappings():
    mappings = defaultdict(dict)
    data_dict = create_text_data_dict()

    for tref in data_dict:
        mappings[Ref(tref).index.title][tref] = data_dict[tref]

    return mappings


def generate_text_post_format(intro_text="", is_intro=False):
    if is_intro:
        intro_text = [intro_text]
    return {
        "text": intro_text,
        "versionTitle": "Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]",
        "versionSource": "talmud.de",
        "language": "en"
    }

def upload_nezikin_intro(intro_dict):
    tref = f"German Commentary on Mishnah, Introduction to Nezikin"
    intro_text = generate_text_post_format(intro_dict["German Commentary on Mishnah, Introduction to Nezikin"], is_intro=True)
    post_text(ref=tref, text=intro_text, server=SEFARIA_SERVER)


def upload_text(mappings):
    intro_dict = process_xml()

    upload_nezikin_intro(intro_dict)

    for book, book_map in mappings.items():
        print(f"Uploading text for {book}")

        if book in intro_dict:
            tref = f"{book}, Introduction"
            intro_text = generate_text_post_format(intro_dict[book], is_intro=True)
            post_text(ref=tref, text=intro_text, server=SEFARIA_SERVER)

        # for tref in book_map:
        #     formatted_text = generate_text_post_format(book_map[tref])
        #     post_text(ref=tref, text=formatted_text, server=SEFARIA_SERVER)


if __name__ == '__main__':
    # TODO - fix to use POST functions?
    # create_term_and_category()
    # print("UPDATE: Terms and categories added")

    # create_index_main()
    # print("UPDATE: Indices created")

    map = create_mappings()
    print("UPDATE: Text map generated")

    upload_text(map)
    print("UPDATE: Text ingest complete")
