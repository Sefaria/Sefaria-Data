import django

django.setup()

import roman
import statistics
import re
import csv
from sefaria.model import *
from sefaria.tracker import modify_bulk_text


# For each new masechet
masechet = ""
# Create a new version
version = Version({"versionTitle": "Talmud Bavli. German. Lazarus Goldschmidt. 1929 [de]",
                   "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH001042448/NLI",
                   "title": f"Mishnah {masechet}",
                   "chapter": [],
                   "language": "en"})

masechet_name = ''
# Modify bulk text for each row in the CSV in this version
with open('german_mishnah_data.csv', newline='') as csvfile:
    german_mishnah = csv.reader(csvfile)
    next(german_mishnah, None)  # skip the headers
    for row in german_mishnah:
        cur_masechet = re.findall(r"Mishnah (.*?) \d.*?:\d.*?$", row[0])[0]
        if masechet_name != cur_masechet:
            masechet_name = cur_masechet
            # Create a new version
            version = Version({"versionTitle": "Talmud Bavli. German. Lazarus Goldschmidt. 1929 [de]",
                               "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH001042448/NLI",
                               "title": f"Mishnah {masechet_name}",
                               "chapter": [],
                               "language": "en"})
            print(f"Modifying for {version}")

        # create dict for modify_bulk_changes
        rowdict = {row[0]: row[1]}
        modify_bulk_text(user=1, version=version, text_map=rowdict, skiplinks=true)
