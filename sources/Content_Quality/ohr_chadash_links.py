from sources.functions import *
import json
ezra_links = {}
import time
with open("/Users/stevenkaplan/sandbox/sefaria-ezra/links/find_query.csv", 'r') as f:
    for row in list(csv.reader(f))[1:]:
        refs = row
        ohr_ref, other_ref = (refs[0], refs[1]) if refs[0].startswith("Ohr Chadash") else (refs[1], refs[0])
        if other_ref.startswith("Footnotes") and ohr_ref.startswith("Ohr Chadash"):
            ezra_links[other_ref] = ohr_ref

current_link = LinkSet({"refs": {"$regex": "Ohr Chadash"}})
prod_links = {}
old = 0
new = 0
new_links = []
for l in current_link:
    refs = l.refs
    ohr_ref, other_ref = (refs[0], refs[1]) if refs[0].startswith("Ohr Chadash") else (refs[1], refs[0])
    if other_ref.startswith("Footnotes") and ohr_ref.startswith("Ohr Chadash"):
        prod_links[other_ref] = ohr_ref

for other_ref in ezra_links:
    new_links.append({"refs": [ezra_links[other_ref], other_ref], "generated_by": "ohr_to_footnotes", "type": "Commentary",
                      "auto": True})

step = 500
init = 0
print(new_links[:init])
#delete_link("Ohr Chadash, Preface 6", server="https://www.sefaria.org")
for i in range(init, len(new_links), step):
    post_link(new_links[init:init+step], server="https://www.sefaria.org")
    print(new_links[init:init+step])
    init += step
    time.sleep(60)

