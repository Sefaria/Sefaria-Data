import django

django.setup()

from sefaria.model import *
from sefaria.helper.schema import convert_simple_index_to_complex, convert_jagged_array_to_schema_with_default, \
    insert_first_child


def convert_children_to_schema_nodes(tref):
    book_title = Ref(tref).index.title
    i = library.get_index(book_title)
    # Convert to Schema nodes
    for ja_node in i.nodes.children:
        if isinstance(ja_node, JaggedArrayNode):
            convert_jagged_array_to_schema_with_default(ja_node)


def create_intro():
    intro = JaggedArrayNode()
    intro.add_structure(["Paragraph"])
    intro.add_shared_term("Introduction")
    intro.key = "Introduction"
    intro.validate()
    return intro


def create_intro_complex_text(node):
    intro = create_intro()
    insert_first_child(intro, node)


def convert_index(node):
    index_title = node.title
    convert_simple_index_to_complex(library.get_index(index_title))
    create_intro_complex_text(Ref(index_title).index_node)


if __name__ == '__main__':
    indices = ["Horayot", "Yadayim", "Oktzin", "Tevul Yom", "Makhshirin"]

    for index_title in indices:
        index = Index().load({"title": f"Rambam on Mishnah {index_title}"})
        print(f"Adding an introduction to {index.title}")
        convert_index(index)
