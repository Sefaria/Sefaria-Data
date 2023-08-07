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


def generate_text_post_format(text):
    return {
        "text": [text],
        "versionTitle": "Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]",
        "versionSource": "talmud.de",
        "language": "en"
    }


def upload_nezikin_intro(intro_dict):
    tref = f"German Commentary, Introduction to Seder Nezikin"
    intro_text = generate_text_post_format(intro_dict["German Commentary, Introduction to Seder Nezikin"])
    post_text(ref=tref, text=intro_text, server=SEFARIA_SERVER)


def upload_text(mappings):
    intro_dict = process_xml()

    upload_nezikin_intro(intro_dict)

    for book in mappings:
        print(f"Uploading text for {book}")

        # if book in intro_dict:
        #     tref = f"{book}, Introduction"
        #     intro_text = generate_text_post_format(intro_dict[book])
        #     post_text(ref=tref, text=intro_text, server=SEFARIA_SERVER)

        formatted_text = generate_text_post_format(mappings[book])
        post_text(ref=f"German Commentary on {book}", text=formatted_text, server=SEFARIA_SERVER)


if __name__ == '__main__':
    # TODO - Run Term/Category cauldron script
    # TODO - fix Nezikin error

    # create_index_main()
    # print("UPDATE: Indices created")

    map = create_text_data_dict()
    print("UPDATE: Text map generated")

    upload_text(map)
    print("UPDATE: Text ingest complete")
