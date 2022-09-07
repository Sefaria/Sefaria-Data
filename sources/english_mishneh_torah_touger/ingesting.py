import django

django.setup()

import csv
from collections import defaultdict
from sefaria.model import *
from sefaria.tracker import modify_bulk_text


def create_mappings():
    mappings = defaultdict(dict)
    with open('mishneh_torah_data_cleaned.csv', newline='') as csvfile:
        mt_csv = csv.DictReader(csvfile)
        for row in mt_csv:
            mt_ref = f"Mishneh Torah, {row['ref']}"
            mappings[Ref(mt_ref).index.title][mt_ref] = row['text']
    return mappings


def create_version_from_scratch(book):
    cur_version = VersionSet({'title': f'{book}',
                              'versionTitle': 'Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007'})
    if cur_version.count() > 0:
        cur_version.delete()
    version = Version({"versionTitle": "Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007",
                       "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH001020101/NLI",
                       "title": f"{book}",
                       "chapter": [],
                       "language": "en",
                       "digitizedBySefaria": True,
                       "license": "CC-BY-NC",
                       "status": "",
                       "versionNote": "© Published and Copyright by Moznaim Publications.<br>Must obtain written permission from Moznaim Publications for any commercial use. Any use must cite Copyright by Moznaim Publications."
                       })
    return version


def upload_text(mappings):
    for book, book_map in mappings.items():
        version = create_version_from_scratch(book)
        print(f"Uploading text for {book}")
        modify_bulk_text(user=142625,
                         version=version,
                         text_map=book_map,
                         skip_links=True,
                         count_after=False)


if __name__ == '__main__':
    map = create_mappings()
    upload_text(map)