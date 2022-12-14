import django

django.setup()

from sefaria.model import *
from sefaria.helper.schema import remove_branch, insert_first_child, attach_branch, \
    insert_last_child, convert_jagged_array_to_schema_with_default


#         - Delete the intro node
#         - Convert existing to default, and then add the other nodes as intros
#         - Add three nodes as subnodes to the likutei amarim node

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


def insert_second_child(new_node, parent_node):
    return attach_branch(new_node, parent_node, 1)

def insert_third_child(new_node, parent_node):
    return attach_branch(new_node, parent_node, 2)


def delete_current_intro_node():
    tanya_index = library.get_index("Tanya")
    tanya_nodes = tanya_index.nodes.children
    for node in tanya_nodes:
        title = node.get_primary_title()
        if title == "Part I; Likkutei Amarim, Compiler's Foreword":
            remove_branch(node)

def create_new_nodes():
    title_page = create_intro("Title Page", "שער")
    approbation = create_intro("Approbation", "הסכמות")
    approbation.depth = 2
    approbation.addressTypes = ["Integer", "Integer"]
    approbation.sectionNames = ["Chapter", "Paragraph"]
    compilers_fwd = create_intro("Compiler's Foreward", "הקדמת המלקט")
    return [{'node': title_page, 'fxn': insert_first_child},
            {'node': approbation, 'fxn': insert_second_child},
            {'node': compilers_fwd, 'fxn': insert_third_child}]
    # insert_first_child(title_page, node)
    # insert_second_child(approbation, node)
    # insert_third_child(compilers_fwd, node)


def insert_nodes():
    new_node_list = create_new_nodes()
    for dict_item in new_node_list:
        tanya_index = library.get_index("Tanya")  # reload index, and refind node each time
        tanya_nodes = tanya_index.nodes.children
        for tnode in tanya_nodes:
            title = tnode.get_primary_title()
            if title == "Part I; Likkutei Amarim":
                fxn = dict_item['fxn']
                node = dict_item['node']
                fxn(node, tnode)


def convert_node():
    tanya_index = library.get_index("Tanya") # reload index, and refind node each time
    tanya_nodes = tanya_index.nodes.children
    for node in tanya_nodes:
        title = node.get_primary_title()
        if title == "Part I; Likkutei Amarim":
            convert_jagged_array_to_schema_with_default(node)


if __name__ == '__main__':
    print("Deleting mistaken node")
    delete_current_intro_node()
    print("Converting Likkutei Amarim to Schema")
    convert_node()
    print("Adding nodes")
    insert_nodes()


# Todo - works on second time, why?
