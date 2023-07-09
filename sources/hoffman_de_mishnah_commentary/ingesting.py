import django

django.setup()

from sefaria.model import *
import csv
from collections import defaultdict
from sefaria.model import *
from sefaria.tracker import modify_bulk_text

def create_mappings():
    mappings = defaultdict(dict)
    with open('', newline='') as csvfile:
        hoffman_csv = csv.DictReader(csvfile)
        for row in hoffman_csv:
            tref = f"{row['ref']}"
            mappings[Ref(tref).index.title][tref] = row['text']
    return mappings


# TODO: Fill in with appropriate details
def create_version_from_scratch(masechet, versionTitle):
    cur_version = VersionSet({'title': f'{masechet}',
                              'versionTitle': versionTitle})
    if cur_version.count() > 0:
        cur_version.delete()
    version = Version({"versionTitle": versionTitle,
                       "versionSource": "",
                       "title": f"{masechet}",
                       "chapter": [],
                       "language": "en",
                       "digitizedBySefaria": True,
                       "license": "CC-BY-NC",
                       "status": "locked",
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
    # Uncomment and run line below if first time through
    # add_chabad_book_names_alt_titles()
    map = create_mappings()
    upload_text(map)
