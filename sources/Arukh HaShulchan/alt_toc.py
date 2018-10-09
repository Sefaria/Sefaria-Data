#encoding=utf-8

import os
import django
django.setup()
from sefaria.model import *
from sources.functions import UnicodeReader, get_index_api, post_index
from sefaria.helper.schema import migrate_to_complex_structure
if __name__ == "__main__":
    files = [f for f in os.listdir('.') if f.endswith(".csv")]
    nodes = []
    for f in files:
        schema = SchemaNode()
        en_title = f.replace(".csv", "")
        he_title = library.get_index(en_title).get_title('he')
        schema.add_primary_titles(en_title, he_title)
        reader = UnicodeReader(open(f))
        for row in reader:
            he, en, first, last = row
            node = ArrayMapNode()
            node.add_primary_titles(en, he)
            node.depth = 0
            node.wholeRef = "Arukh HaShulchan, {} {}-{}".format(en_title, first, last)
            node.refs = []
            schema.append(node)
        nodes.append(schema.serialize())

    index = get_index_api("Arukh HaShulchan", server="http://draft.sefaria.org")
    index['alt_structs'] = {"Subject": {"nodes": nodes}}
    # post_index(index, server="http://draft.sefaria.org")
    mapping = {
        "Aruch HaShulchan 1": "Arukh HaShulchan, Orach Chaim",
        "Aruch HaShulchan 2": "Arukh HaShulchan, Yoreh Deah",
        "Aruch HaShulchan 3": "Arukh HaShulchan, Even HaEzer",
        "Aruch HaShulchan 4": "Arukh HaShulchan, Choshen Mishpat"
    }
    root = SchemaNode()
    root.add_primary_titles("Arukh HaShulchan", u"ערוך השולחן")
    nodes = [("Orach Chaim", u"אורח חיים"), ("Yoreh De'ah", u"יורה דעה"), ("Even HaEzer", u"אבן העזר"), ("Choshen Mishpat", u"חושן משפט")]
    for node in nodes:
        ja_node = JaggedArrayNode()
        ja_node.add_primary_titles(node[0], node[1])
        ja_node.key = node[0]
        ja_node.add_structure(["Siman", "Paragraph"])
        ja_node.depth = 2
        root.append(ja_node)
    schema = root.serialize()
    index = {"title": "Arukh HaShulchan", "schema": schema, "categories": ["Halakhah"]}

    migrate_to_complex_structure("Aruch HaShulchan", schema, mapping)