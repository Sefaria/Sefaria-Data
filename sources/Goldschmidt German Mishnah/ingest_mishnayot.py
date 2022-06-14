import django

django.setup()

import csv
from collections import defaultdict
from sefaria.model import *
from sefaria.tracker import modify_bulk_text


def create_mappings():
    mappings = defaultdict(dict)
    with open('german_mishnah_data.csv', newline='') as csvfile:
        german_mishnah_csv = csv.DictReader(csvfile)
        for row in german_mishnah_csv:
            mappings[Ref(row['mishnah_tref']).index.title][row['mishnah_tref']] = row['de_text']
    return mappings


def create_version_from_scratch(masechet):
    cur_version = VersionSet({'title': f'{masechet}',
                              'versionTitle': 'Talmud Bavli. German. Lazarus Goldschmidt. 1929 [de]'})
    if cur_version.count() > 0:
        cur_version.delete()
    version = Version({"versionTitle": "Talmud Bavli. German. Lazarus Goldschmidt. 1929 [de]",
                       "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH001042448/NLI",
                       "title": f"{masechet}",
                       "chapter": [],
                       "language": "en"})
    return version


def upload_text(mappings):
    for masechet, masechet_map in mappings.items():
        version = create_version_from_scratch(masechet)
        print(f"Uploading text for {masechet}")
        modify_bulk_text(user=142625,
                         version=version,
                         text_map=masechet_map,
                         skip_links=True,
                         count_after=False)


if __name__ == '__main__':
    map = create_mappings()
    upload_text(map)
