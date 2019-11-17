#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *
import csv
prev_alt_struct = prev_ref = ""
bayit_cheder = [{} for count in range(202)]
with open("ravpninim - ravpninim.csv") as f:
    for row in list(csv.reader(f))[1:]:
        alt_struct = row[2]
        ref = row[0]
        link = row[3]
        # if alt_struct.split(":")[0] not in bayit_cheder:
        #     bayit_cheder[alt_struct.split(":")[0]] = {}

        if alt_struct and not prev_alt_struct:
            prev_alt_struct = alt_struct
            bayit_cheder[int(alt_struct.split(":")[0]) - 1][alt_struct.split(":")[1]] = ref

        if alt_struct != prev_alt_struct:
            prev_val = bayit_cheder[int(prev_alt_struct.split(":")[0]) - 1][prev_alt_struct.split(":")[1]]
            if prev_val != prev_ref:
                bayit_cheder[int(prev_alt_struct.split(":")[0]) - 1][prev_alt_struct.split(":")[1]] = prev_val + "-" + prev_ref.split()[-1]
            bayit_cheder[int(alt_struct.split(":")[0]) - 1][alt_struct.split(":")[1]] = ref

        prev_alt_struct = alt_struct
        prev_ref = ref

prev_val = bayit_cheder[int(alt_struct.split(":")[0]) - 1][alt_struct.split(":")[1]]
if prev_val != ref:
    bayit_cheder[int(alt_struct.split(":")[0]) - 1][alt_struct.split(":")[1]] = prev_val + "-" + ref.split()[-1]

nodes = []
for bayit, chadarim in enumerate(bayit_cheder):
    node = ArrayMapNode()
    node.add_primary_titles("House {}".format(bayit+1), u"בית {}".format(numToHeb(bayit+1)))
    node.add_structure(["Room"])
    node.depth = 1
    refs = []
    first = None
    j = 0
    for i in range(len(chadarim.keys())):
        if bayit == 16 and i == 8:
            j = 1
        refs += [chadarim[str(i+1+j)]]
        if i == 0:
            first = refs[-1]
        assert refs[-1].count("-") in [0, 1]
    node.refs = refs
    node.wholeRef = first.split("-")[0] + "-" + refs[-1].split()[-1].split("-")[-1]
    assert node.wholeRef.count("-") == 1
    node.validate()
    nodes.append(node.serialize())


index = get_index_api("Rav Peninim on Proverbs", server="http://ste.sandbox.sefaria.org")
index['alt_structs'] = {"Houses": {"nodes": nodes}}
post_index(index)


