import django

django.setup()

import csv
from collections import defaultdict
from sefaria.model import *
from sources.functions import post_text
from sources.local_settings import SEFARIA_SERVER


def create_mappings():
    mappings = defaultdict(dict)
    with open("my_sample_commentary_text.csv", 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            tref = row['ref']
            text = row['text']
            mappings[Ref(tref).index.title][tref] = text

    return mappings


def generate_text_post_format(intro_text="", require_intro_format=False):
    if require_intro_format:
        intro_text = [intro_text]
    return {
        "text": intro_text,
        "versionTitle": "My Sample Commentary - Dummy Data for Templating Purposes",
        "versionSource": "www.mysamplecommentary.data",
        "versionNotes": "Notes, or a dedication would go here",
        "language": "en"
    }


def upload_text(mappings):

    for book, book_map in mappings.items():
        print(f"Uploading text for {book}")

        for tref in book_map:
            formatted_text = generate_text_post_format(book_map[tref])
            post_text(ref=tref, text=formatted_text, server=SEFARIA_SERVER)


if __name__ == '__main__':

    mapper = create_mappings()
    print("UPDATE: Text map generated")

    upload_text(mapper)
    print("UPDATE: Text ingest complete")