from sources.functions import *
from sefaria.helper.schema import *
intro = JaggedArrayNode()
intro.add_shared_term("Introduction")
intro.key = "Introduction"
intro.add_structure(["Paragraph"])
convert_simple_index_to_complex(library.get_index("Radak on I Chronicles"))
insert_first_child(intro, library.get_index("Radak on I Chronicles").nodes)
