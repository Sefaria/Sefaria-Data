import django
django.setup()
import csv
from sefaria.model import *
for book in library.get_indexes_in_category("Tanakh"):
    if book in ["Ezra", "I Chronicles", "II Chronicles", "Nehemiah", "Daniel"]:
        print(book)
        continue
    i = library.get_index(book)
    for sec_ref in i.all_section_refs():
        polish_section = TextChunk(sec_ref, lang='en', vtitle="Bible in Polish, trans. Izaak Cylkow, 1841 - 1908 [pl]").text
        orig_section = TextChunk(sec_ref).text
        if len(polish_section) != len(orig_section):
            print("{} difference in {}".format(len(orig_section)-len(polish_section), sec_ref))
        for seg_ref in sec_ref.all_segment_refs():
            polish_text = TextChunk(seg_ref, lang='en', vtitle="Bible in Polish, trans. Izaak Cylkow, 1841 - 1908 [pl]").text
            orig_text = TextChunk(seg_ref).text
            if not polish_text:
                print(seg_ref)

