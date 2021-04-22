import django
django.setup()
import csv
import sys
from sources.functions import *
new_file = ""
import os
import csv
files = [f for f in os.listdir(".") if f.endswith(".csv")]
for new_file in files:
    # if "Moed" not in new_file or "Rosh" not in new_file:
    #     continue
    print(new_file)
with open("Leshon_Chakhamim") as f:
    reader = list(csv.reader(f))
    title = reader[0][1]
    vtitle = reader[1][1]
    lang = reader[2][1]
    vsource = reader[3][1]
    text = {}
    for row in reader[5:]:
        ref, comm = row
        tc = TextChunk(Ref(ref), lang=lang, vtitle=vtitle)
        tc.text = comm
        tc.save(force_save=True)
    #     chapter, segment = ref.split()[-1].split(":")
    #     chapter = int(chapter)
    #     segment = int(segment)
    #     if chapter not in text:
    #         text[chapter] = {}
    #     text[chapter][segment] = comm
    # start_at = -1
    # for chapter in text:
    #     if chapter < start_at:
    #         continue
    #     text[chapter] = convertDictToArray(text[chapter])
    #     send_text = {"language": lang, "versionSource": vsource, "versionTitle": vtitle,
    #                  "text": text[chapter]}
    #     post_text("{} {}".format(title, chapter), send_text, server="https://www.sefaria.org")
