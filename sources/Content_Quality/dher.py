from linking_utilities.dibur_hamatchil_matcher import *
for r in library.get_index("Chidushei Agadot on Sotah").all_section_refs():
    daf = r.normal().replace("Chidushei Agadot on ", "")
    base = Ref(f"Sotah {daf}").text('he')
    comments = TextChunk(r, lang='he', vtitle='Vilna Edition')

    match_ref(base, comments, lambda x: x.split(), dh_extract_method)