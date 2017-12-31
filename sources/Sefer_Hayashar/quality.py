from sefaria.model import *
from sefaria.helper.schema import *

def add_default_node():
    index = library.get_index("Sefer HaYashar")
    root = index.nodes

    default = JaggedArrayNode()
    default.key = "default"
    default.default = True
    default.add_structure(["Chapter", "Paragraph"])

    attach_branch(default, root, 1)


def remove_chapter_nodes():
    index = library.get_index("Sefer HaYashar")
    root = index.nodes

    for node in root.children:
        title = node.get_titles("en")[0]
        if "CHAPTER" in title:
            remove_branch(node)
        elif "Addendum" in title:
            new_title = " ".join(node.get_titles("en")[0].split(" ")[2:])
            node.remove_title(title, "en")
            node.add_title(new_title, "en", primary=True)
        elif "Footnotes" in title:
            remove_branch(node)

if __name__ == "__main__":
    remove_chapter_nodes()
    add_default_node()
