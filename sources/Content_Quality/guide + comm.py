import django
import sys
django.setup()
from sefaria.model import *
from sefaria.helper.schema import *

title = sys.argv[1]


def needs_rewrite_2(string, *args):
    return string.startswith(f"{title}, Part 2 Introduction")


def needs_rewrite_3(string, *args):
    return string.startswith(f"{title}, Part 3 Introduction")


def needs_rewrite(string, *args):
    return string.startswith(f"{title}")





if __name__ == "__main__":
    # for title in ["Guide for the Perplexed", "Efodi on Guide for the Perplexed",
    #               "Crescas on Guide for the Perplexed", "Shem Tov on Guide for the Perplexed"]:
    print(title)
    place = 0 if title != "Guide for the Perplexed" else 1
    print("Converting JA to schema")
    i = library.get_index(f"{title}")
    convert_jagged_array_to_schema_with_default(i.nodes.children[1+place])
    i = library.get_index(f"{title}")
    convert_jagged_array_to_schema_with_default(i.nodes.children[3+place])
    i = library.get_index(f"{title}")
    convert_jagged_array_to_schema_with_default(i.nodes.children[5+place])
    if title == 'Guide for the Perplexed':
        print("Moving Introduction")
        i = library.get_index(f"{title}")
        node = i.nodes.children[0].children[1]  # Ibn Tibon
        print(node)
        change_parent(node, i.nodes, place=0, exact_match=True)

        i = library.get_index(f"{title}")
        print(i.nodes.children[1])
        remove_branch(i.nodes.children[1])

    i = library.get_index(f"{title}")
    node = i.nodes.children[0+place].children[0]
    print(node)
    change_parent(node, i.nodes, place=place, exact_match=True)

    i = library.get_index(f"{title}")
    node = i.nodes.children[1+place].children[0]
    print(node)
    change_parent(node, i.nodes, place=place+1, exact_match=True)

    print("Creating fake node")
    fake_node = JaggedArrayNode()
    fake_node.key = "fake"
    fake_node.add_primary_titles("fake", "fake hebrew")
    fake_node.add_structure(["Paragraph"])
    fake_node.validate()
    i = library.get_index(f"{title}")
    attach_branch(fake_node, i.nodes.children[place+2])

    i = library.get_index(f"{title}")
    node = i.nodes.children[place+2].children[1]
    print(node)
    change_parent(node, i.nodes.children[place+3], place=0, exact_match=True)

    i = library.get_index(f"{title}")
    remove_branch(i.nodes.children[place+2])

    print("Moving Part II and Part III Introduction")
    i = library.get_index(f"{title}")
    node = i.nodes.children[place+3]
    change_parent(node, i.nodes.children[place+4], place=0, exact_match=True)

    i = library.get_index(f"{title}")
    node = i.nodes.children[place+4]
    change_parent(node, i.nodes.children[place+5], place=0, exact_match=True)

    i = library.get_index(f"{title}")
    print(i.nodes.children)
    node = i.nodes.children[place+3].children[0]
    change_node_title(node, "Part 2 Introduction", 'en', 'Introduction', ignore_cascade=True)
    change_node_title(node, "חלק ב' הקדמה", 'he', 'הקדמה')

    i = library.get_index(f"{title}")
    node = i.nodes.children[place+4].children[0]
    change_node_title(node, "Part 3 Introduction", 'en', 'Introduction', ignore_cascade=True)
    change_node_title(node, "חלק ג' הקדמה", 'he', 'הקדמה')

    rewriter = lambda x: x.replace(f"{title}, Part 2 Introduction", f"{title}, Part 2, Introduction")
    cascade(f"{title}", rewriter=rewriter, needs_rewrite=needs_rewrite_2)

    rewriter = lambda x: x.replace(f"{title}, Part 2, Part 2 Introduction", f"{title}, Part 2, Introduction")
    cascade(f"{title}", rewriter=rewriter, needs_rewrite=lambda string, *args: string.startswith(f"{title}, Part 2, Part 2 Introduction"))

    rewriter = lambda x: x.replace(f"{title}, Part 3, Part 3 Introduction", f"{title}, Part 3, Introduction")
    cascade(f"{title}", rewriter=rewriter, needs_rewrite=lambda string, *args: string.startswith(f"{title}, Part 3, Part 3 Introduction"))

    rewriter = lambda x: x.replace(f"{title}, Part 3 Introduction", f"{title}, Part 3, Introduction")
    cascade(f"{title}", rewriter=rewriter, needs_rewrite=needs_rewrite_3)

    rewriter = lambda string: string.replace(f"{title}, Introduction, Letter to R Joseph son of Judah",
                   f"{title}, Letter to R Joseph son of Judah")
    cascade(f"{title}", rewriter=rewriter, needs_rewrite=lambda string, *args: string.startswith("Guide for the Perplexed, Introduction, Letter to R Joseph son of Judah"))

    rewriter = lambda string: string.replace(f"{title}, Introduction, Prefatory Remarks",
                   f"{title}, Prefatory Remarks")
    cascade(f"{title}", rewriter=rewriter, needs_rewrite=lambda string, *args: string.startswith("Guide for the Perplexed, Introduction, Prefatory Remarks"))

    rewriter = lambda string: string.replace(f"{title}, Introduction, Introduction",
                   f"{title}, Part 1, Introduction")
    cascade(f"{title}", rewriter=rewriter, needs_rewrite=lambda string, *args: string.startswith("Guide for the Perplexed, Introduction, Introduction"))

    if title == "Guide for the Perplexed":
        rewriter = lambda string: string.replace(f"{title}, Introduction, Introduction of Ibn Tibon",
                                                 f"{title}, Introduction of Ibn Tibon")
        cascade(f"{title}", rewriter=rewriter, needs_rewrite=lambda string, *args: string.startswith("Guide for the Perplexed, Introduction, Introduction of Ibn Tibon"))
