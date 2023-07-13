import django

django.setup()

from sefaria.model import *
import csv
from collections import defaultdict
from sefaria.model import *
from sefaria.tracker import modify_bulk_text, modify_text
from sources.functions import post_text
from sources.hoffman_de_mishnah_commentary.extract_commentary import create_text_data_dict
from sources.hoffman_de_mishnah_commentary.parse_intro_xml import process_xml

## Stuck here on Modify-Bulk-Text issues with the introduction. Once resolved, put up on cauldron for QA, clean code, and push

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
                       "status": "unlocked",
                       })
    version.save()


def generate_text_post_format(text):
    return {
        "text": [text],
        "versionTitle": "Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]",
        "versionSource": "talmud.de",
        "language": "en"
    }


def upload_text(mappings):
    for book, book_map in mappings.items():
        create_version_from_scratch(book, "Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]")
        print(f"Uploading text for {book}")

        intro_dict = process_xml()
        tref = "German Commentary on Mishnah Berakhot, Introduction"
        text = generate_text_post_format(intro_dict["Traktat Berachot"])
        post_text(ref=tref, text=text, server="http://localhost:8000")
        # for tref in book_map:
        #     text = generate_text_post_format(book_map[tref])
        #     post_text(ref=tref, text=text, server="http://localhost:8000")


if __name__ == '__main__':
    map = create_mappings()
    upload_text(map)
