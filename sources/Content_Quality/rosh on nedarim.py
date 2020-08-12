from sources.functions import *
start_ref = Ref("Commentary of the Rosh on Nedarim 66a")
links = []
with open("find_query.csv") as f:
    for i, row in enumerate(csv.reader(f)):
        if i is 0:
            continue
        refs = row[7], row[8]
        rosh = 0 if refs[0].startswith("Commentary of the Rosh on Nedarim") else 1
        assert refs[rosh].startswith("Commentary of the Rosh on Nedarim")
        rosh_ref = refs[rosh]
        other_ref = refs[1-rosh]
        follows_start_ref = Ref(rosh_ref).section_ref().follows(start_ref)
        links.append({"refs": refs, "generated_by": row[1], "type": "Commentary", "auto": True})

post_link(links, server="https://www.sefaria.org")