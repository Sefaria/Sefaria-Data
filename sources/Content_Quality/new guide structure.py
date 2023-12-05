import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import *
title = "Guide for the Perplexed"

def needs_rewrite_2(string, *args):
    return string.startswith(f"{title}, Part 2 Introduction")

def needs_rewrite_3(string, *args):
    return string.startswith(f"{title}, Part 3 Introduction")

def needs_rewrite(string, *args):
    return string.startswith(f"{title}")

def convert_jas():
    print("Converting JA to schema")
    i = library.get_index(f"{title}")
    convert_jagged_array_to_schema_with_default(i.nodes.children[2])
    i = library.get_index(f"{title}")
    convert_jagged_array_to_schema_with_default(i.nodes.children[4])
    i = library.get_index(f"{title}")
    convert_jagged_array_to_schema_with_default(i.nodes.children[6])

if __name__ == "__main__":
    convert_jas()

    if title == 'Guide for the Perplexed':
        print("Moving Introduction")
        i = library.get_index(f"{title}")
        node = i.nodes.children[0].children[1]      # Ibn Tibon
        print(node)
        change_parent(node, i.nodes, place=0, exact_match=True)

        i = library.get_index(f"{title}")
        print(i.nodes.children[1])
        remove_branch(i.nodes.children[1])

    i = library.get_index(f"{title}")
    node = i.nodes.children[1].children[0]
    print(node)
    change_parent(node, i.nodes, place=1, exact_match=True)

    i = library.get_index(f"{title}")
    node = i.nodes.children[2].children[0]
    print(node)
    change_parent(node, i.nodes, place=2, exact_match=True)

    print("Creating fake node")
    fake_node = JaggedArrayNode()
    fake_node.key = "fake"
    fake_node.add_primary_titles("fake", "fake hebrew")
    fake_node.add_structure(["Paragraph"])
    fake_node.validate()
    i = library.get_index(f"{title}")
    attach_branch(fake_node, i.nodes.children[3])

    i = library.get_index(f"{title}")
    node = i.nodes.children[3].children[1]
    change_parent(node, i.nodes.children[4], place=0, exact_match=True)

    i = library.get_index(f"{title}")
    remove_branch(i.nodes.children[3])

    print("Moving Part II and Part III Introduction")
    i = library.get_index(f"{title}")
    node = i.nodes.children[4]
    change_parent(node, i.nodes.children[5], place=0, exact_match=True)

    i = library.get_index(f"{title}")
    node = i.nodes.children[5]
    change_parent(node, i.nodes.children[6], place=0, exact_match=True)

    i = library.get_index(f"{title}")
    print(i.nodes.children)
    node = i.nodes.children[4].children[0]
    change_node_title(node, "Part 2 Introduction", 'en', 'Introduction', ignore_cascade=True)

    i = library.get_index(f"{title}")
    node = i.nodes.children[5].children[0]
    change_node_title(node, "Part 3 Introduction", 'en', 'Introduction', ignore_cascade=True)

    rewriter = lambda x: x.replace(f"{title}, Part 2 Introduction", f"{title}, Part 2, Introduction")
    cascade(f"{title}", rewriter=rewriter, needs_rewrite=needs_rewrite_2)

    rewriter = lambda x: x.replace(f"{title}, Part 3 Introduction", f"{title}, Part 3, Introduction")
    cascade(f"{title}", rewriter=rewriter, needs_rewrite=needs_rewrite_3)


#
#
# ----> 3 cascade(f"{title}", rewriter=rewriter, needs_rewrite=needs_rewrite)
#       4
#       5 rewriter = lambda x: x.replace(f"{title}, Part 3 Introduction", f"{title}, Part 3, Introduction")
#
# /app/sefaria/helper/schema.py in cascade(ref_identifier, rewriter, needs_rewrite, skip_history)
#     707     generic_rewrite(GardenStopSet(construct_query('ref', identifier)))
#     708     print('Updating Sheets')
# --> 709     clean_sheets([s['id'] for s in db.sheets.find(construct_query('sources.ref', identifier), {"id": 1})])
#     710     print('Updating Alternate Structs')
#     711     update_alt_structs(ref_identifier.index)
#
# /app/sefaria/helper/schema.py in clean_sheets(sheets_to_update)
#     653                 print("Likely error - can't load sheet {}".format(sid))
#     654             for source in sheet["sources"]:
# --> 655                 if rewrite_source(source):
#     656                     needs_save = True
#     657             if needs_save:
#
# /app/sefaria/helper/schema.py in rewrite_source(source)
#     630                 original_tref = source["ref"]
#     631                 try:
# --> 632                     rewrite = needs_rewrite(source["ref"])
#     633                 except (InputError, ValueError) as e:
#     634                     print('needs_rewrite method threw exception:', source["ref"], e)
#
# TypeError: <lambda>() missing 1 required positional argument: 'x'
