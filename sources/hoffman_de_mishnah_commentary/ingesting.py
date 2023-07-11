import django

django.setup()

from sefaria.model import *
import csv
from collections import defaultdict
from sefaria.model import *
from sefaria.tracker import modify_bulk_text
from sources.hoffman_de_mishnah_commentary.extract_commentary import create_text_data_dict

def create_mappings():
    mappings = defaultdict(dict)
    data_dict = create_text_data_dict()
    for tref in data_dict:
        if "Berakhot" in tref: #Todo, temp filter, eventually remove
            mappings[Ref(tref).index.title][tref] = data_dict[tref]
    return mappings


# TODO: Fill in with appropriate details
def create_version_from_scratch(title, versionTitle):
    cur_version = VersionSet({'title': f'{title}',
                              'versionTitle': versionTitle})
    if cur_version.count() > 0:
        cur_version.delete()
    version = Version({"versionTitle": versionTitle,
                       "versionSource": "talmud.de",
                       "title": f'{title}',
                       "chapter": [],
                       "language": "en",
                       "digitizedBySefaria": True,
                       "license": "Public Domain",
                       # "status": "locked",
                       })
    return version


def upload_text(mappings):
    for book, book_map in mappings.items():
        version = create_version_from_scratch(book, "Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]")
        print(f"Uploading text for {book}")
        modify_bulk_text(user=142625,
                         version=version,
                         text_map=book_map,
                         skip_links=True,
                         count_after=False)


if __name__ == '__main__':
    map = create_mappings()
    upload_text(map)
