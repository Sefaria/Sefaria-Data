import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError
from sources.functions import *
import re

index = get_index_api("Zohar", server="http://ste.sandbox.sefaria.org")
post_index(index, server="http://www.sefaria.org")
get_text

def get_pos(looking_for, text_ste):
    refs = []
    looking_for = looking_for.replace("(", "\(").replace(")", "\)")
    for pos in [m.start() for m in re.finditer(u"{}".format(looking_for), text_ste)]:
        while text_ste[pos] != "Z":
            pos += 1

        refs.append(re.search("^(Zohar .*?)\n", text_ste[pos:]).group(1))
    return refs

new_start = []
new_end = []
with open("zohar alt toc.txt") as f:
    for i, line in enumerate(f):
        if i % 3 == 1:
            after_ref = line.strip()
            new_start.append(after_ref)

new_start = list(reversed(new_start))
for i, ref in enumerate(new_start):
    new_end_ref = Ref(new_start[i+1]) if i+1 < len(new_start) else Ref("Zohar 3:299b:14")
    new_end.append(new_end_ref.prev_segment_ref())



#
# text_to_ref_ste_version = {}
# text_ste = ""
# with open("zohar3.csv") as f:
#     for n, line in enumerate(f):
#         text, ref = line.split(":Zohar", 1)
#         ref = "Zohar" + ref
#         assert "Zohar" not in text
#         assert "Zohar" in ref
#         if int(ref.split()[-1].split(":")[1].replace("b", "").replace("a", "")) < 56:
#             continue
#         text_to_ref_ste_version[text.decode('utf-8')] = ref
#         text_ste += line.decode('utf-8') + "\n"
index = get_index_api("Zohar")
nodes = index["alt_structs"]["Parasha"]["nodes"]
changed_nodes = []
starting_at = -1
for i, node in enumerate(nodes):
    if "sharedTitle" in node and node["sharedTitle"] == "Vayera":
        starting_at = i
        node["wholeRef"] = "Zohar 1:97a:1-1:120b:8"
    elif starting_at >= 0:
        wholeRef = Ref(node["wholeRef"])
        start_ref = wholeRef.starting_ref()
        end_ref = wholeRef.ending_ref()
        start_ref.sections[1] += 1
        start_ref.toSections[1] += 1
        end_ref.sections[1] += 1
        end_ref.toSections[1] += 1
        new_range = Ref(_obj=start_ref._core_dict()).to(Ref(_obj=end_ref._core_dict()))
        node["wholeRef"] = new_range.normal()

    if "Zohar 2" in node["wholeRef"]:
        break

starting_at = -1
for i, node in enumerate(nodes):
    if "sharedTitle" in node and node["sharedTitle"] == "Achrei Mot":
        starting_at = i
    if starting_at >= 0:
        try:
            node["wholeRef"] = Ref(new_start[i-starting_at]).to(new_end[i-starting_at]).normal()
        except InputError as e:
            print node
index['alt_structs'] = {"Parasha": {"nodes": nodes}}
post_index(index, server="http://ste.sandbox.sefaria.org")

# for node in relevant_nodes:
#     zohar_range = Ref(node["wholeRef"])
#     start = zohar_range.starting_ref()
#     old_start_text = start.text('he').text
#     end = zohar_range.ending_ref()
#     old_end_text = end.text('he').text
#     looking_for = u" ".join(old_start_text.split()[0:20])
#     looking_for = looking_for.replace("<b>", "").replace("</b>", "")
#     new_start = get_pos(looking_for, text_ste)
#     if not new_start:
#         pass
#
#     print start
#     print new_start
#     print
