import django
django.setup()
import csv
from sources.functions import *
links = []
with open("rae_eh_new.csv") as f:
    for row in UnicodeReader(f):
        if not row[0].startswith("Rabbi Akiva"):
            continue
        ref, text, link_1, link_2 = row
        for other_ref in [link_1, link_2]:
            if u"\u05ea" in ref+other_ref:
                print
            links.append({"refs": [ref, other_ref], "generated_by": "Akiva Eger", "type": "Commentary", "auto": True})
post_link(links)