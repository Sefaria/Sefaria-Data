from sources.yavetz.link import *
title = "Chidushei Agadot on Sotah"
index = library.get_index(title)
index.versionState().refresh()
base = library.get_index(index.base_text_titles[0])
if 'Mishnah' in base.categories:
    link_misnah(title)
elif 'Bavli' in base.categories:
    link_bavli(title, server="https://editingtools2.cauldron.sefaria.org")
#
# from linking_utilities.dibur_hamatchil_matcher import *
#
# for r in library.get_index("Chidushei Agadot on Sotah").all_section_refs():
#     daf = r.normal().replace("Chidushei Agadot on ", "")
#     base = Ref(f"Sotah {daf}").text('he')
#     comments = TextChunk(r, lang='he', vtitle='Vilna Edition')
#
#     match_ref(base, comments, lambda x: x.split(), dh_extract_method)