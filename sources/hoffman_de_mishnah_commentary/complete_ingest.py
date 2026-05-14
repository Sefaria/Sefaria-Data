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


def create_mappings():
    mappings = defaultdict(dict)
    data_dict = create_text_data_dict()

    for tref in data_dict:
        mappings[Ref(tref).index.title][tref] = data_dict[tref]

    return mappings


def generate_text_post_format(intro_text="", require_intro_format=False):
    if require_intro_format:
        intro_text = [intro_text]
    return {
        "text": intro_text,
        "versionTitle": "Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]",
        "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002378149/NLI",
        "versionNotes": "Ordnung Seraïm, übers. und erklärt von Ascher Samter. 1887.<br>Ordnung Moed, von Eduard Baneth. 1887-1927.<br>Ordnung Naschim, von Marcus Petuchowski u. Simon Schlesinger. 1896-1933.<br>Ordnung Nesikin, von David Hoffmann. 1893-1898.<br>Ordnung Kodaschim, von John Cohn. 1910-1925.<br>Ordnung Toharot, von David Hoffmann, John Cohn und Moses Auerbach. 1910-1933.",
        "language": "en"
    }


def upload_intros(intro_dict):
    tref = f"German Commentary, Introduction to Seder Nezikin"
    intro_text = generate_text_post_format(intro_dict["German Commentary, Introduction to Seder Nezikin"],
                                           require_intro_format=False) # different structure than other intros
    post_text(ref=tref, text=intro_text, server=SEFARIA_SERVER)

    tref="German Commentary, Introduction"
    with open("general_intro_to_mishnah.txt", "r") as f:
        general_text = f.read()
    intro_text = generate_text_post_format(general_text, require_intro_format=True) # different structure than other intros
    post_text(ref=tref, text=intro_text, server=SEFARIA_SERVER)


def upload_text(mappings):
    intro_dict = process_xml()

    upload_intros(intro_dict)

    for book, book_map in mappings.items():
        print(f"Uploading text for {book}")

        if book in intro_dict:
            tref = f"{book}, Introduction"
            intro_text = generate_text_post_format(intro_dict[book], require_intro_format=True)
            post_text(ref=tref, text=intro_text, server=SEFARIA_SERVER)

        for tref in book_map:
            formatted_text = generate_text_post_format(book_map[tref])
            post_text(ref=tref, text=formatted_text, server=SEFARIA_SERVER)


if __name__ == '__main__':
    # TODO - Run Term/Category cauldron script

    # create_index_main()
    # print("UPDATE: Indices created")

    # If errors before mapping, trying running admin/reset/cache, then admin/reset/toc, then admin/reset/cache
    # and run just from the stage below.

    mapper = create_mappings()
    print("UPDATE: Text map generated")

    upload_text(mapper)
    print("UPDATE: Text ingest complete")
