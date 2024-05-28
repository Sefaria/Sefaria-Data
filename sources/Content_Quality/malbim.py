import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import *

books = ["Malbim on Joshua", "Malbim on Isaiah", "Malbim on Ezekiel", "Malbim on Song of Songs", "Malbim on Psalms"]
for b in books:
    print(b)
    new_node = JaggedArrayNode()
    new_node.add_shared_term("Introduction")
    new_node.add_structure(["Paragraph"])
    new_node.key = "Introduction"
    new_node.validate()
    book = library.get_index(b)
    convert_simple_index_to_complex(book)
    book = library.get_index(b)
    insert_first_child(new_node, book.nodes)