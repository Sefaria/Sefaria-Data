import django

django.setup()

import roman
import statistics
import re
import csv
from sefaria.model import *
from sefaria.tracker import modify_bulk_text

masechet_name = ''
# Modify bulk text for each row in the CSV in this version
with open('german_mishnah_data.csv', newline='') as csvfile:
    german_mishnah = csv.DictReader(csvfile)
    for row in german_mishnah:
        cur_masechet = Ref(row['mishnah_tref']).index.title
        if masechet_name != cur_masechet:
            if masechet_name:
                # Skip the first empty one
                print(f"Modifying for {masechet_name}")
                modify_bulk_text(user=142625,
                                 version=version,
                                 text_map=version_dict,
                                 skip_links=True,
                                 count_after=False)
            # clear version_dict
            version_dict = {}
            masechet_name = cur_masechet
            # Create a new version
            cur_version = VersionSet({'title': f'{masechet_name}',
                                      'versionTitle': 'Talmud Bavli. German. Lazarus Goldschmidt. 1929 [de]'})
            if cur_version.count() > 0:
                cur_version.delete()
            version = Version({"versionTitle": "Talmud Bavli. German. Lazarus Goldschmidt. 1929 [de]",
                               "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH001042448/NLI",
                               "title": f"{masechet_name}",
                               "chapter": [],
                               "language": "en"})

        # As long as it's in the same version, append the tref and text
        version_dict[row['mishnah_tref']] = row['de_text']

    print(f"Modifying for {masechet_name}")  # hit the last masechet
    modify_bulk_text(user=142625,
                     version=version,
                     text_map=version_dict,
                     skip_links=True,
                     count_after=False)
