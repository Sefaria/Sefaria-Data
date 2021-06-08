import django
django.setup()
from sefaria.helper.schema import *
def create_intro():
    intro = JaggedArrayNode()
    intro.add_structure(["Paragraph"])
    intro.add_shared_term("Introduction")
    intro.key = "Introduction"
    intro.validate()
    return intro

i = library.get_index("Tur")
intro = create_intro()
insert_first_child(intro, i.nodes)

i = library.get_index("Beit Yosef")
intro = create_intro()
insert_first_child(intro, i.nodes)
