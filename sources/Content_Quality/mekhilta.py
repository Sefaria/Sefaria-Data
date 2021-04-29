from sources.functions import *

alt_toc = """Massekta dePesah / מסכתא דפסחא
Exodus 12:1–13:16
Massekta deVayehi Beshalach / מסכתא דויהי בשלח
Exodus 13:17-14:31
Massekta deShirah / מסכתא דשירה
Exodus 15:1-15:21
Massekta deVayassa / מסכתא דויסע
Exodus 15:22-17:7
Massekta deAmalek / מסכתא דעמלק
Exodus 17:8- 18:27
Massekta deBahodesh / מסכתא דבחודש
Exodus 19:1-20:26
Massekta deNezikin / מסכתא דנזיקין
Exodus 21:1-22:23
Massekta deKaspa / מסכתא דכספא
Exodus 22:24-23:19
Massekta deShabbeta / מסכתא דשבתא
Exodus 31:12-35:3"""
nodes = []
alt_toc = alt_toc.splitlines()
for r, row in enumerate(alt_toc):
    if r % 2 == 0:
        node = ArrayMapNode()
        en, he = row.strip().split(" / ")
        node.add_primary_titles(en, he)
        node.depth = 0
        node.refs = []
    else:
        node.wholeRef = row.strip().replace("Exodus", "Mekhilta d'Rabbi Yishmael")
        node.validate()
        nodes.append(node.serialize())

index = get_index_api("Mekhilta d'Rabbi Yishmael", server="https://germantalmud.cauldron.sefaria.org")
index["alt_structs"] = {"Parasha": {"nodes": nodes}}
#post_index(index, server="https://www.sefaria.org")

links = []
for sec_ref in library.get_index("Mekhilta d'Rabbi Yishmael").all_section_refs():
    seg_ref = sec_ref.as_ranged_segment_ref().normal()
    exodus_ref = sec_ref.normal().replace("Mekhilta d'Rabbi Yishmael", "Exodus")
    print(exodus_ref)
    print(seg_ref)
    print("***")
    links.append({"refs": [exodus_ref, seg_ref], "generated_by": "mekhilta_to_exodus", "auto": True, "type": "Commentary"})
post_link_in_steps(links, server="https://www.sefaria.org", step=100, sleep_amt=10)