import django

django.setup()

import csv
from sefaria.model import *
from sefaria.helper.schema import convert_simple_index_to_complex, convert_jagged_array_to_schema_with_default, \
    insert_first_child, attach_branch
from sources.functions import add_term



# Uncomment on first run - Run this first, pointing at the required server
# add_term("An Introduction by the Author's Son", 'הקדמת בן המחבר', server="")


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
    book_title = Ref(tref).index.title
    i = library.get_index(book_title)
    # Convert to Schema nodes
    for ja_node in i.nodes.children:
        if isinstance(ja_node, JaggedArrayNode):
            convert_jagged_array_to_schema_with_default(ja_node)


def check_if_double_intro(row):
    return row["Intro Position"] != ""


def separate_row_data(row):
    en_title = row[0]['Intro English Title']
    he_title = row[0]['Intro Hebrew Title']
    pos = row[0]['Intro Position']
    pos = int(pos) if pos != '' else ''
    double_intros = row[0]['double_intros']
    return en_title, he_title, pos, double_intros


def handle_node_with_hakdamot_for_each_child(index_dict, node_title, en_title, he_title, pos):
    for item in index_dict[node_title]:
        child_tref = item['Parent Ref']
        convert_children_to_schema_nodes(child_tref)
        create_intro_complex_text(child_tref, en_title, he_title, pos)


def handle_simple_index(node, node_title, en_title, he_title):
    if not node.parent and not node.children:
        index_title = Ref(node_title).index.title
        convert_simple_index_to_complex(library.get_index(index_title))
        create_intro_complex_text(node_title, en_title, he_title)


def create_index_dict():
    with open('intros_08_09_2022.csv', newline='') as csvfile:
        german_mishnah_csv = csv.DictReader(csvfile)
        index_dict = {}
        for row in german_mishnah_csv:

            # Copy row to new dict for modifying purposes
            flagged_row = row.copy()

            # Check if it's one of the 'double introduction' rows
            is_double_intro = check_if_double_intro(flagged_row)

            # Set flags accordingly
            flagged_row['double_intros'] = is_double_intro

            # Append to the index dictionary by Book Title (key)
            idx_title = Ref(row['Parent Ref']).index.title
            if idx_title in index_dict:
                index_dict[idx_title].append(flagged_row)
            else:
                index_dict[idx_title] = [flagged_row]
    # print(index_dict)
    return index_dict


def run(index_dict):
    for node_title in index_dict:

        node = Ref(node_title).index_node

        print(f"Attempting to handle {node_title}")

        row = index_dict[node_title]
        en_title, he_title, pos, double_intros = separate_row_data(row)

        # A node where each child has its own hakdamah (i.e. Hakdama to Bereshit, Hakdama to Shemot)
        # and those children need to be converted from JA Nodes to Schema nodes
        if len(row) > 1 and not double_intros:
            handle_node_with_hakdamot_for_each_child(index_dict, node_title, en_title, he_title, pos)

        # Converting a simple index to a complex one, before adding the intro
        elif isinstance(node, JaggedArrayNode):  # Simple index
            handle_simple_index(node, node_title, en_title, he_title)

        # The node already exists as a schema node
        else:  # Schema node (BY case)
            # Add multiple introductions if necessary
            if double_intros:
                for item in index_dict[node_title]:
                    tref = item['Parent Ref']
                    en_title = item['Intro English Title']
                    he_title = item['Intro Hebrew Title']
                    pos = int(item['Intro Position'])
                    create_intro_complex_text(tref, en_title, he_title, pos)
            # Add the single introduction if only one
            else:
                create_intro_complex_text(node_title, en_title, he_title, pos)


if __name__ == '__main__':
    idx_dict = create_index_dict()
    run(idx_dict)
