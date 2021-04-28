from sources.functions import *
def dher(str):
    str = re.search("<b>(.*?)</b>", str)
    if str:
        str = str.group(1)
        if len(str.split(" ")) < 3:
            return ""
        str = str.replace("ה'", "יהוה")
        str = str.split("וגו'")[0]
        return str
    else:
        return ""

i = library.get_index("Ohev Yisrael")
matches = []
ref_pairs = []
for n in i.nodes.children[-1].children:
    parasha = n.ref().normal().replace("Ohev Yisrael, Selections, ", "")
    if parasha.startswith("Parashat"):
        base = parasha
    else:
        base = "Parashat " + parasha
    ref_pairs.append((base, n.ref()))

for n in i.nodes.children[-7].children:
    base = n.ref().normal().replace("Ohev Yisrael, Selections on Nach, ", "")
    ref_pairs.append((base, n.ref()))

for n in i.nodes.children[4:]:
    parasha = n.ref().normal().replace("Ohev Yisrael, ", "")
    if parasha.startswith("Parashat"):
        base = parasha
    else:
        base = "Parashat "+parasha
    try:
        Ref(base)
        for r in n.ref().all_subrefs():
            ref_pairs.append((base, r))
    except:
        pass

for base, n in ref_pairs:
    try:
        comments = [c.text('he').text for c in n.all_segment_refs()]
        matches += match_ref_interface(base, n.normal(), comments, lambda x: x.split(), dher, vtitle="Tanach with Text Only")
    except:
        print(n)
        xyz = False
        if xyz:
            comments = [c.text('he').text for c in n.all_segment_refs()]
            matches += match_ref_interface(base, n.normal(), comments, lambda x: x.split(), dher,
                                           vtitle="Tanach with Text Only")

print(matches)
print(len(matches))
post_link_in_steps(matches, server="https://www.sefaria.org")