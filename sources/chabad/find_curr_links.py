from sources.functions import *
from research.link_disambiguator.main import *
titles = ["Sources and References on Torah Ohr", "Sources and References on Likkutei Torah"]
links = []
no_links = []
ld = Link_Disambiguator()
for t in titles:
    for ref in tqdm(library.get_index(t).all_segment_refs()):
        text = ref.text('he').text
        try:
            dh, after_dh = text.split(":", 1)
        except:
            print(ref)
        after_dh = bleach.clean(after_dh, tags=[], strip=True)
        dhs_and_comm = after_dh.split(".")
        existing_link = Link().load({"$and": [{"refs": ref.normal()}, {"refs": {"$regex": t.replace("Sources and References on ", "")}}]})
        if existing_link is None:
            no_links.append(ref.normal())
        else:
            base_ref = existing_link.refs[0] if existing_link.refs[1].startswith(t) else existing_link.refs[1]
            for poss_dh in dhs_and_comm:
                refs = library.get_refs_in_string("("+poss_dh+")", "he")
                for r in refs:
                    if r.is_section_level():
                        results = disambiguate_one(ld, base_ref, TextChunk(base_ref, lang='he'), ref, TextChunk(ref, lang='he'))
                    if r:
                        links.append({"generated_by": "LT_to_Tanakh", "auto": True, "refs": [r.normal(), base_ref]})
with open('no_links.csv', 'w') as f:
    w = csv.writer(f)
    for l in no_links:
        w.writerow([l, Ref(l).text('he').text])
with open('new_links.json', 'w') as f:
    json.dump(links, f)
