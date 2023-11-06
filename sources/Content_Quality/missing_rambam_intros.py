import django

django.setup()

from sefaria.model import *
from sefaria.helper.schema import convert_simple_index_to_complex, insert_first_child


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


def convert_index(index):
    convert_simple_index_to_complex(index)
    create_intro_complex_text(Ref(index.title).index_node)


if __name__ == '__main__':
    indices = [  "Tevul Yom", "Makhshirin",
                "Horayot",
                "Yadayim",
                 "Oktzin"
                ]

    for index_title in indices:
        idx = library.get_index(f"Rambam on Mishnah {index_title}")
        print(f"Adding an introduction to {idx.title}")
        convert_index(idx)
