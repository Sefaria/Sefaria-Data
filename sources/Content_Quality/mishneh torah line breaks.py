import django
django.setup()
from sefaria.model import *
import re

def action(segment_str, tref, he_tref, version):
    if "<br>" not in segment_str:
        return segment_str
    segment_str = segment_str.replace("<br> <br>", "<br>")
    found_double = False
    while "<br><br>" in segment_str:
        print("DOUBLE BR")
        found_double = True
        segment_str = segment_str.replace("<br><br>", "<br>")

    missing_space = False
    for tuple in re.findall("(.{1})<br>(.{1})", segment_str):
        if tuple[0] != " " and tuple[1] != " ":
            segment_str = segment_str.replace(f"{tuple[0]}<br>{tuple[1]}", f"{tuple[0]} <br>{tuple[1]}")
            missing_space = True
    if missing_space or found_double:
        tc = TextChunk(Ref(tref), lang=version.language, vtitle=version.versionTitle)
        if segment_str != tc.text:
            print(tref)
            tc.text = segment_str
            tc.save()
        return segment_str
    return segment_str

books = library.get_indexes_in_category("Mishneh Torah")
for b in books:
    b = library.get_index(b)
    for v in b.versionSet():
        v.walk_thru_contents(action)
