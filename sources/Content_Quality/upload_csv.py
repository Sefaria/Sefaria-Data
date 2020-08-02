import django
django.setup()
import csv
import sys
from sources.functions import *
with open(sys.argv[1]) as f:
    reader = list(csv.reader(f))
    title = reader[0][1]
    vtitle = reader[1][1]
    lang = reader[2][1]
    vsource = reader[3][1]
    text = {}
    for row in reader[5:]:
        ref, comm = row
        chapter, segment = ref.split()[-1].split(":")
        chapter = int(chapter)
        segment = int(segment)
        if chapter not in text:
            text[chapter] = {}
        text[chapter][segment] = comm
    start_at = 322
    for chapter in text:
        if chapter < start_at:
            continue
        text[chapter] = convertDictToArray(text[chapter])
        send_text = {"language": lang, "versionSource": vsource, "versionTitle": vtitle,
                     "text": text[chapter]}
        post_text("{} {}".format(title, chapter), send_text, server="https://www.sefaria.org")
