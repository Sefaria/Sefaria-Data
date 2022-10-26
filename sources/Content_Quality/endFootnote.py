import django
django.setup()
from sefaria.model import *
import re
vtitle = "Tanakh: The Holy Scriptures, published by JPS"

for i in library.get_indexes_in_category("Tanakh"):
    for ref in library.get_index(i).all_segment_refs():
        tc = TextChunk(ref, lang='en', vtitle=vtitle)
        for find in re.findall("<sup>(-[a-z]{1})</sup>", tc.text):
            tc.text = tc.text.replace(f"<sup>{find}</sup>", f"<sup class='endFootnote'>{find}</sup>")
            print(ref)
            tc.save(force_save=True)

