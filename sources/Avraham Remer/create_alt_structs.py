import os
from sources.functions import *
files = os.listdir(".")
for f in files:
    if f.endswith("csv"):
        title = f.replace(".csv", "")
        alt_node = SchemaNode()
        alt_node.add_primary_titles("Chapter", "פרק")
        alt_node.key = "Chapter"
        with open(f, 'r') as open_f:
            for row in csv.reader(open_f):
                ref, alt_title = row
                child_node = ArrayMapNode()
                child_node.add_primary_titles("Chapter {}".format(ref), alt_title)
                child_node.depth = 0
                child_node.wholeRef = "{} {}".format(title, ref)
                alt_node.append(child_node)
            alt_node.validate()

        index = get_index_api(title, server="https://ezradev.cauldron.sefaria.org")
        index["alt_structs"] = {"Chapters": alt_node.serialize()}
        post_index(index, server="https://ezradev.cauldron.sefaria.org")