import django

django.setup()

import csv
from collections import defaultdict
from sefaria.model import *
from sefaria.tracker import modify_bulk_text


def create_mappings(csv_name, ref_name, text_name, index_title):
    mappings = defaultdict(dict)
    with open(csv_name, newline='') as csvfile:
        sar_csv = csv.DictReader(csvfile)
        for row in sar_csv:
            print(f"mapping {row[ref_name]}")
            mappings[index_title][row[ref_name]] = row[text_name]
    return mappings


def create_version_from_scratch(index_title):
    index = library.get_index(index_title)
    chapter = index.nodes.create_skeleton()
    cur_version = VersionSet({'title': index_title,
                              'versionTitle': 'Kehot Publication Society'})
    if cur_version.count() > 0:
        cur_version.delete()
    version = Version({'versionTitle': 'Kehot Publication Society',
                       "versionSource": "https://store.kehotonline.com/",
                       "title": index_title,
                       "chapter": chapter,
                       "language": "he",
                       "digitizedBySefaria": True,
                       "license": "Public Domain",
                       "status": "locked",
                       "versionNotes": "© Kehot Publication Society"
                       })
    return version


def upload_text(mappings, index_title):
    print(f"ingesting text of {index_title}")
    modify_bulk_text(user=142625,
                     version=version,
                     text_map=mappings[index_title],
                     skip_links=True,
                     count_after=False)


if __name__ == '__main__':
    print("creating version")

    # Shulchan Arukh HaRav
    index_title = "Shulchan Arukh HaRav"
    version = create_version_from_scratch(index_title)
    sar_map = create_mappings(csv_name="shulchan_arukh_harav_text.csv",
                              ref_name="sar_tref",
                              text_name="sar_text",
                              index_title=index_title)
    upload_text(sar_map, index_title=index_title)

    # Kuntres Acharon on Shulchan Arukh HaRav
    index_title="Kuntres Acharon on Shulchan Arukh HaRav"
    version = create_version_from_scratch(index_title)
    ka_map = create_mappings(csv_name="kuntres_acharon_text.csv",
                             ref_name="ka_tref",
                             text_name="ka_text",
                             index_title=index_title)
    upload_text(ka_map, index_title=index_title)
