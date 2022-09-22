import django

django.setup()

import csv
import re
from sefaria.model import *
from sefaria.helper.schema import convert_simple_index_to_complex, convert_jagged_array_to_schema_with_default, \
    insert_first_child, attach_branch
from sources.functions import add_term


# Todo
# Handle position - throwing the issue
# Handle Legends of the Jews
# It seems to be failing on Maggid Devarav L'Yakov as well, but working for all of the other texts... work through 2 intro cases


# TODO
# Add this to schema and import
def insert_second_child(new_node, parent_node):
    return attach_branch(new_node, parent_node, 1)


def create_intro(en_title, he_title):
    intro = JaggedArrayNode()
    intro.add_structure(["Paragraph"])
    if en_title == "Introduction":
        intro.add_shared_term(en_title)
    else:
        intro.add_primary_titles(en_title, he_title)
    intro.key = en_title
    intro.validate()
    return intro


def create_intro_complex_text(tref, en_title, he_title, pos=None):
    node = Ref(tref).index_node
    intro = create_intro(en_title, he_title)
    if pos == 2:
        insert_second_child(intro, node)
    else:  # if 1 or no position specified
        insert_first_child(intro, node)


def convert_children_to_schema_nodes(tref):
    i = library.get_index(tref)
    # Convert to Schema nodes
    for ja_node in i.nodes.children:
        if isinstance(ja_node, JaggedArrayNode):
            convert_jagged_array_to_schema_with_default(ja_node)


def create_index_dict():
    with open('intros_08_09_2022.csv', newline='') as csvfile:
        german_mishnah_csv = csv.DictReader(csvfile)
        index_dict = {}
        former_parent_tref = None
        new_row = {}
        for row in german_mishnah_csv:

            # If first row
            if not former_parent_tref:
                former_parent_tref = row['Parent Ref']

            is_double_intro = False
            parent_tref = row['Parent Ref']

            if parent_tref == former_parent_tref:
                new_row = row
                new_row['two_intros'] = True
                is_double_intro = True

            i = library.get_index(parent_tref)
            idx_title = re.findall(r"Index: (.*)", str(i))[0]

            if idx_title in index_dict:
                if former_parent_tref != parent_tref:
                    index_dict[idx_title].append(row)
                else:
                    index_dict[idx_title].append(new_row)
            else:
                if is_double_intro:
                    index_dict[idx_title] = [new_row]
                else:
                    index_dict[idx_title] = [row]
    print(index_dict)
    return index_dict


def run(index_dict):
    for node_title in index_dict:

        seen = False

        two_intros = False

        node = Ref(node_title).index_node

        print(f"Attempting to handle {node_title}")

        row = index_dict[node_title]
        en_title = row[0]['Intro English Title']
        he_title = row[0]['Intro Hebrew Title']
        pos = row[0]['Intro Position']

        if 'two_intros' in row[0]:
            two_intros = True


        if len(row) > 1 and not two_intros:  # Multiple indices for the children
            seen = True

            for item in index_dict[node_title]:
                child_tref = item['Parent Ref']
                convert_children_to_schema_nodes(child_tref)
                create_intro_complex_text(child_tref, en_title, he_title, pos)

        elif isinstance(node, JaggedArrayNode):  # Simple index
            if not node.parent and not node.children:
                seen = True
                convert_simple_index_to_complex(library.get_index(node_title))
                create_intro_complex_text(node_title, en_title, he_title)
        else:  # Schema node (BY case)
            if len(row) > 1 and two_intros:
                seen = True
                for item in index_dict[node_title]:
                    tref = item['Parent Ref']
                    en_title = item['Intro English Title']
                    he_title = item['Intro Hebrew Title']
                    create_intro_complex_text(tref, en_title, he_title, pos)
            else:
                seen = True
                create_intro_complex_text(node_title, en_title, he_title, pos)

        if not seen:
            print(f"ERROR: {node_title} was not addressed by this script")


if __name__ == '__main__':
    idx_dict = create_index_dict()
    run(idx_dict)
