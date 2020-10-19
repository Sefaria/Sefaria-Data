import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import change_node_title

i = library.get_index("Ohr Chadash")
intro = i.nodes.children[0]
preface = i.nodes.children[1]
change_node_title(intro, "Introduction to Ohr Chadash", 'en', "Introduction")
change_node_title(intro, "", 'he', "")