from sources.functions import *
index = get_index_api("Leshon Chakhamim", server="https://germantalmud.cauldron.sefaria.org")
with open("Leshon_Chakhamim_-_alt_toc.csv", 'r') as f:
    ref = ""
    nodes = []
    part_1 = SchemaNode()
    part_1.add_primary_titles("Part I", "חלק ראשון")
    part_1.key = "Part I"
    part_1.validate()
    part_2 = SchemaNode()
    part_2.add_primary_titles("Part II", "חלק שני")
    part_2.key = "Part II"
    part_2.validate()

    for row in csv.reader(f):
        if len(row[0]) > 0:
            ref = row[0]
        seg_ref = row[1]
        curr_leshon_ref = "{} {}".format(ref, seg_ref)
        title = curr_leshon_ref.replace("Leshon Chakhamim, Part II", "").replace("Leshon Chakhamim, Part I", "")
        print(curr_leshon_ref)
        alt_ref = row[2]
        alt_node = ArrayMapNode()
        alt_node.add_primary_titles("Section "+title, alt_ref)
        alt_node.depth = 0
        alt_node.wholeRef = curr_leshon_ref
        alt_node.refs = []
        alt_node.validate()
        if "Part II" in ref:
            part_2.append(alt_node)
        else:
            part_1.append(alt_node)
part_1.validate()
part_2.validate()
nodes.append(part_1.serialize())
nodes.append(part_2.serialize())
index["alt_structs"] = {"Section": {"nodes": nodes}}
post_index(index, server="https://germantalmud.cauldron.sefaria.org")