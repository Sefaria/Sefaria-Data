import django
django.setup()
from sefaria.model import *
for i in library.get_indexes_in_category("Bavli"):
    if i.startswith("Chatam"):
        continue
    print(i)
    index = library.get_index("Mishnah {}".format(i))
    library.refresh_index_record_in_cache(index)
    for ref in index.all_segment_refs():
        text = TextChunk(ref, vtitle="William Davidson Edition - English", lang="en").text
        if not text:
            print(ref)
