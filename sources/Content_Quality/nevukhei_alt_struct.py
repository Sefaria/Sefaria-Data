from sources.functions import *
import csv
index = get_index_api("LeNevukhei HaTekufah", server="https://germantalmud.cauldron.sefaria.org")
with open("LeNevukhei_HaTekufah_-_alt.csv", 'r') as f:
    rows = list(csv.reader(f))[1:]
    curr_heb_sec = ""
    curr_eng_sec = ""
    nodes = []
    node = None
    node_num = 0
    for row in rows:
        heb_sec, eng_sec, eng_ch, heb_ch = row
        if len(heb_sec) > 0:
            curr_heb_sec = heb_sec
            curr_eng_sec = eng_sec
            if node:
                node.validate()
                nodes.append(node.serialize())
            node_num += 1
            node = SchemaNode()
            node.add_primary_titles(curr_eng_sec, curr_heb_sec)
        child = ArrayMapNode()
        child.add_primary_titles(eng_ch, heb_ch)
        child.refs = []
        child.depth = 0
        child.wholeRef = "LeNevukhei HaTekufah {}:{}".format(node_num, eng_ch)
        child.validate()
        node.append(child)

    nodes.append(node.serialize())
    index["alt_structs"] = {"Topic": {"nodes": nodes}}
post_index(index, server="https://germantalmud.cauldron.sefaria.org")