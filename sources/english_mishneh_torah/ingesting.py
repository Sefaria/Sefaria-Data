import django

django.setup()

import csv
from collections import defaultdict
from sefaria.model import *
from sefaria.tracker import modify_bulk_text


# TODO - double check this code based on final CSV format
def create_mappings():
    mappings = defaultdict(dict)
    with open('mishneh_torah_data_FINAL.csv', newline='') as csvfile:
        mt_csv = csv.DictReader(csvfile)
        for row in mt_csv:
            mappings[Ref(row['ref']).index.title][row['ref']] = row['text']
    return mappings


def create_version_from_scratch(book):
    cur_version = VersionSet({'title': f'{book}', # todo - add
                              'versionTitle': ''}) # todo - add
    if cur_version.count() > 0:
        cur_version.delete()
    version = Version({"versionTitle": "", # todo - add
                       "versionSource": "", # todo - add
                       "title": f"", # todo - add
                       "chapter": [],
                       # TODO - check the following flags
                       "language": "en",
                       "digitizedBySefaria": True,
                       "license": "Public Domain",
                       "status": "locked"
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