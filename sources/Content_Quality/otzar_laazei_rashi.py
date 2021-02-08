from sources.functions import *

#delete_link("Otzar Laazei Rashi, Talmud", server="https://www.sefaria.org")
#delete_link("Otzar Laazei Rashi, Tanakh", server="https://www.sefaria.org")

ls = LinkSet({"refs": {"$regex": "Otzar Laazei Rashi"}}).array()
print(len(ls))
new_ls = []
already_found = []
for i, l in enumerate(ls):
    l = l.contents()
    l.pop("source_text_oid")
    otzar_ref, other_ref = (l["refs"][0], l["refs"][1]) if l["refs"][0].startswith("Otzar") else (l["refs"][1], l["refs"][0])

    if Ref(other_ref).is_section_level() or (otzar_ref, other_ref) in already_found:
        pass
    else:
        already_found.append((otzar_ref, other_ref))
        new_ls.append({"refs": l["refs"], "generated_by": l["generated_by"], "auto": l["auto"], "type": l["type"]})
        if new_ls[-1]["type"] == "":
            new_ls[-1]["type"] = "Commentary"

print(len(new_ls))
post_link_in_steps(new_ls, server="https://www.sefaria.org")

