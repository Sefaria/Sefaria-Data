import django

django.setup()

import csv
from collections import defaultdict
from sefaria.model import *
from sefaria.tracker import modify_bulk_text


def create_mappings():
    mappings = defaultdict(dict)
    with open('french_mishnah_cleaned.csv', newline='') as csvfile:
        french_mishnah_csv = csv.DictReader(csvfile)
        for row in french_mishnah_csv:
            mappings[Ref(row['mishnah_tref']).index.title][row['mishnah_tref']] = row['yerushalmi_french_text']
    return mappings


def create_version_from_scratch(masechet):
    cur_version = VersionSet({'title': f'{masechet}',
                              'versionTitle': 'Le Talmud de Jérusalem, traduit par Moise Schwab, 1878-1890 [fr]'})
    if cur_version.count() > 0:
        cur_version.delete()
    version = Version({"versionTitle": "Le Talmud de Jérusalem, traduit par Moise Schwab, 1878-1890 [fr]",
                       "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002182155/NLI",
                       "title": f"{masechet}",
                       "chapter": [],
                       "language": "en",
                       "license": "Public Domain",
                       "status": "locked"
                       })
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