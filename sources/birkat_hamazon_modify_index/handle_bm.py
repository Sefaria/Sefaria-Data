import django

django.setup()
from sefaria.model import *
from sefaria.helper.schema import *

if __name__ == '__main__':
    bm_index = library.get_index("Birkat Hamazon")
    main_parent = bm_index.nodes
    children_to_hoist = bm_index.nodes.children[0].children
    # print("Creating fake node")
    # fake_node = JaggedArrayNode()
    # fake_node.key = "fake"
    # fake_node.add_primary_titles("fake", "fake hebrew")
    # fake_node.add_structure(["Paragraph"])
    # fake_node.validate()
    # attach_branch(fake_node, bm_index.nodes.children[0], 6)
    for i, child in enumerate(children_to_hoist):
        if i == 6:
            break
        bm_index = library.get_index("Birkat Hamazon")
        main_parent = bm_index.nodes
        children_to_hoist = bm_index.nodes.children[i].children
        change_parent(child, main_parent)
    remove_branch(bm_index.nodes.children[0])
    print("bye")
