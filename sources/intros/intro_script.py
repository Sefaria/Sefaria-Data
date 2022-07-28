import django

django.setup()

import csv
import re
from sefaria.model import *
from sefaria.helper.schema import convert_simple_index_to_complex, convert_jagged_array_to_schema_with_default, \
    insert_first_child

def create_intro():
    intro = JaggedArrayNode()
    intro.add_structure(["Paragraph"])
    intro.add_shared_term("Introduction")
    intro.key = "Introduction"
    intro.validate()
    return intro


def create_intro_complex_text(tref):
    node = Ref(tref).index_node
    intro = create_intro()
    insert_first_child(intro, node)


def convert_children_to_schema_nodes(tref):
    i = library.get_index(tref)
    # Convert to Schema nodes
    for ja_node in i.nodes.children:
        if isinstance(ja_node, JaggedArrayNode):
            convert_jagged_array_to_schema_with_default(ja_node)


def create_index_dict():
    with open('sample_intros_7_25_22.csv', newline='') as csvfile:
        german_mishnah_csv = csv.DictReader(csvfile)
        index_dict = {}
        for row in german_mishnah_csv:
            parent_tref = row['Parent Ref']

            if row["Intro Address Types"] or row["Intro Section Names"] or row["Intro Position"]:
                print("Contains a specific address, section or position type")
                raise Exception()

            i = library.get_index(parent_tref)
            idx_title = re.findall(r"Index: (.*)", str(i))[0]

            if idx_title in index_dict:
                index_dict[idx_title].append(row)
            else:
                index_dict[idx_title] = [row]
    return index_dict


def run(index_dict):
    for node_title in index_dict:

        node = Ref(node_title).index_node

        print(node)

        if len(index_dict[node_title]) > 1:  # Multiple indices for the children
            print("Converting children from JA to schema nodes")
            for child in node.children:
                child_tref = str(child)
                print(f"Up to {child_tref}")
                convert_children_to_schema_nodes(child_tref)
                create_intro_complex_text(child_tref)

        if isinstance(node, JaggedArrayNode):  # Simple index
            if not node.parent and not node.children:
                print("Converting simple index to complex")
                convert_simple_index_to_complex(library.get_index(node_title))
                create_intro_complex_text(node_title)
        else:  # Schema node (BY case)
            print("Adding intro to an existing schema node")
            i = library.get_index(node_title)
            intro = create_intro()
            insert_first_child(intro, i.nodes)


if __name__ == '__main__':
    idx_dict = create_index_dict()
    run(idx_dict)
