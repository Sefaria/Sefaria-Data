import django
django.setup()
from sefaria.helper.schema import *

def create_intro():
    intro = JaggedArrayNode()
    intro.add_structure(["Paragraph"])
    intro.add_shared_term("Introduction")
    intro.key = f"Introduction"
    intro.validate()
    return intro

i = library.get_index("Tur")
# # Convert to Schema nodes
# for ja_node in i.nodes.children:
#     convert_jagged_array_to_schema_with_default(ja_node)

for schema_node in i.nodes.children:
    intro = create_intro()
    insert_first_child(intro, schema_node)




