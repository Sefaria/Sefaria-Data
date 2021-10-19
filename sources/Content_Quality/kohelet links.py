from sources.functions import *
ls = [l.contents() for l in LinkSet({"refs": {"$regex": "^Ecclesiastes"}})]
# old = {sorted([l.refs[0], l.refs[1]]) for l in LinkSet({"refs": {"$regex": "^Ecclesiastes"}})}
# existing = get_links("Ecclesiastes", server="https://www.sefaria.org")
# existing_set = set()
# for link in existing:
#     ref1, ref2 = link["anchorRef"], link["sourceRef"]
#     existing_set.add(sorted([ref1, ref2]))
#
#
# for link in old:
#     if old not in existing_set:
#
new_links = []
for l in ls:
    new_links.append({"refs": [l["refs"][0], l["refs"][1]], "auto": l["auto"], "generated_by": l["generated_by"],
                      "type": l["type"]})
print(ls.count())
#post_link_in_steps(new_links, step=300, sleep_amt=7, server="https://www.sefaria.org")