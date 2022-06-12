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
    german_mishnah = csv.reader(csvfile)
    next(german_mishnah, None)  # skip the headers
    for row in german_mishnah:
        cur_masechet = re.findall(r"Mishnah (.*?) \d.*?:\d.*?$", row[0])[0]
        if masechet_name != cur_masechet:
            # Run modify bulk changes on the past masechet
            if masechet_name:
                # Skip the first empty one
                print(f"Modifying for {masechet_name}")
                modify_bulk_text(user=1, version=version, text_map=version_dict, skip_links=True)
            # clear version_dict
            version_dict = {}
            masechet_name = cur_masechet
            # Create a new version
            version = Version({"versionTitle": "Talmud Bavli. German. Lazarus Goldschmidt. 1929 [de]",
                               "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH001042448/NLI",
                               "title": f"Mishnah {masechet_name}",
                               "chapter": [],
                               "language": "en"})

        # As long as it's in the same version, append the tref and text
        tref = row[0]
        text = row[1]
        version_dict[tref] = text

    print(f"Modifying for {masechet_name}") # hit the last masechet
    modify_bulk_text(user=1, version=version, text_map=version_dict, skip_links=True)


