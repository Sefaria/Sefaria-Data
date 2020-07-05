import django
django.setup()
import csv
from sources.functions import *
import os
import re
for f in os.listdir("."):
    text = {}
    if f.endswith("txt"):
        title = u" ".join(f.split(".txt")[:-1])
        prev_daf = 3
        text[prev_daf] = []
        with open(f) as file:
            lines = list(file)
            for n, line in enumerate(lines):
                poss_daf = re.search("[@\d(]{3,4}דף \S{1,} \S{1,} ", line)
                if poss_daf:
                    marker, daf, amud = poss_daf.group(0).split()
                    amud = getGematria(amud)
                    if amud not in [1, 2, 71, 72]:
                        amud = 1 if "'" in daf else 2
                    curr_daf = (getGematria(daf)*2) - (amud % 2)
                    if curr_daf - prev_daf <= 0:
                        print("{}\n{}{} after {}\n".format(f, line, curr_daf, prev_daf))
                    elif curr_daf - prev_daf > 7:
                        curr_daf = getGematria(daf[0])*2 - (amud % 2)
                    prev_daf = curr_daf
                    text[curr_daf] = []
                    line = line.replace(poss_daf.group(0), "")
                text[prev_daf].append(line)
        try:
            en_title = library.get_index(title).title
        except:
            continue
        text = convertDictToArray(text)
        send_text = {
            "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002036613/NLI",
            "versionTitle": "Chidushei Chatam Sofer, 1864-1908",
            "text": text,
            "language": "he"
        }
        root = JaggedArrayNode()
        root.add_structure(["Daf", "Paragraph"], address_types=["Talmud", "Integer"])
        root.add_primary_titles("Chatam Sofer on {}".format(en_title), u"חתם סופר על {}".format(title))
        root.validate()
        indx = {
            "schema": root.serialize(),
            "title": "Chatam Sofer on {}".format(en_title),
            "categories": ["Talmud", "Bavli", "Commentary", "Chatam Sofer"]
        }
        post_index(indx)
        post_text("Chatam Sofer on {}".format(en_title), send_text)

