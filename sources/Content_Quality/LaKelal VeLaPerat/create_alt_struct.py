from sources.functions import *

with open("alt_struct.csv") as f:
    en = he = ""
    parent_node = None
    root = []
    vol = "I"
    # root = SchemaNode()
    # root.add_primary_titles("Gate", "שאר")
    for row in csv.reader(f):
        curr_he, curr_en, segment, he_title = row

        if curr_he:
            if curr_en.startswith("10"):
                vol = "II"
            elif curr_en.startswith("17"):
                vol = "III"

            he = curr_he
            en = curr_en
            if parent_node:
                parent_node.validate()
                root.append(parent_node.serialize())
            parent_node = SchemaNode()
            parent_node.add_primary_titles(en, he)
            parent_node.key = en
        ref = "LaKelal VeLaPerat, Volume {}, {} {}".format(vol, en, segment)
        child_node = ArrayMapNode()
        child_node.add_primary_titles(segment, he_title)
        child_node.depth = 0
        child_node.refs = []
        child_node.wholeRef = ref
        parent_node.append(child_node)
    parent_node.validate()
    root.append(parent_node.serialize())
index = get_index_api("LaKelal VeLaPerat", server="https://ste.cauldron.sefaria.org")
index["alt_structs"] = {"Gate": {"nodes": root}}
Index(index)
post_index(index, server="https://ste.cauldron.sefaria.org")

