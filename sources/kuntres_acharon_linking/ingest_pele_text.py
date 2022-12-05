import django

django.setup()

import csv
from collections import defaultdict
from sefaria.model import *
from sefaria.tracker import modify_bulk_text

# NOTE: Index on PELE is entirely different than the existing index for Shulchan Aruch HaRav
# It will need to change on prod to match as well eventually, but this code does not handle that
# (I copied manually the document from the cauldron to my local)
# If needed, happy to write code to rework the index into its new format


def create_mappings():
    mappings = defaultdict(dict)
    with open('sar-he.csv', newline='') as csvfile:
        sar_csv = csv.DictReader(csvfile)
        for row in sar_csv:
            print(f"mapping {row['sar_tref']}")
            mappings['Shulchan Arukh HaRav'][row['sar_tref']] = row['sar_text']
    return mappings


def create_version_from_scratch():
    index = library.get_index("Shulchan Arukh HaRav")
    chapter = index.nodes.create_skeleton()
    cur_version = VersionSet({'title': 'Shulchan Arukh HaRav',
                              'versionTitle': 'Kehot Publication Society'})
    if cur_version.count() > 0:
        cur_version.delete()
    version = Version({'versionTitle': 'Kehot Publication Society',
                       "versionSource": "https://store.kehotonline.com/",
                       "title": 'Shulchan Arukh HaRav',
                       "chapter": chapter,
                       "language": "he",
                       "digitizedBySefaria": True,
                       "license": "Public Domain",
                       "status": "locked",
                       "versionNotes": "© Kehot Publication Society"
                       })
    return version


def upload_text(mappings):
    print("ingesting text")
    modify_bulk_text(user=142625,
                     version=version,
                     text_map=mappings['Shulchan Arukh HaRav'],
                     skip_links=True,
                     count_after=False)


if __name__ == '__main__':
    print("creating version")
    version = create_version_from_scratch()

    map = create_mappings()
    upload_text(map)
