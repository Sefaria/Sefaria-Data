from sources.functions import *
books = library.get_indices_by_collective_title("Migdal Oz")
for b in tqdm(books):
    if "Mishneh Torah" in b:
        change = False
        b = library.get_index(b)
        prev_text = ""
        for ref in b.all_section_refs():
            tc = TextChunk(ref, lang='he', vtitle='Friedberg Edition')
            if tc.text == prev_text and len(prev_text) > 0:
                new_tc = TextChunk(ref, lang='he', vtitle='Friedberg Edition')
                new_tc.text = []
                print(ref)
                new_tc.save()
                change = True
            prev_text = tc.text
        if change:
            print("Refreshing")
            vs = VersionState(index=b)
            vs.refresh()

books = library.get_indices_by_collective_title("Migdal Oz")
for b in tqdm(books):
    if "Mishneh Torah" in b:
        change = True
        b = library.get_index(b)
        if change:
            vs = VersionState(index=b)
            vs.refresh()
