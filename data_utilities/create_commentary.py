#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *
import sys
base_title = sys.argv[1]
comm_title = sys.argv[2]
comm_sections = sys.argv[3].split(", ")
comm_full_en_title = "{} on {}".format(comm_title, base_title)
base_index = library.get_index(base_title)
base_he = base_index.get_title('he')
comm_he = Term().load({"name": comm_title}).get_primary_title('he')
comm_full_he_title = u"{} על {}".format(comm_he, base_he)
comm_index = Index()
root = JaggedArrayNode()
root.add_primary_titles(comm_full_en_title, comm_full_he_title)
root.key = comm_full_en_title
comm_depth = base_index.nodes.depth + 1
assert len(comm_sections) is comm_depth and type(comm_sections) is list
root.depth = comm_depth
root.add_structure(comm_sections)
root.validate()
indx = {
    "title": comm_full_en_title,
    "schema": root.serialize(),
    "categories": ["Halakhah", "Commentary"],
    "collective_title": comm_title,
    "base_text_titles": [base_title],
    "base_text_mapping": "one_to_one",
    "dependence": "Commentary"
}
post_index(indx, server="http://ste.sandbox.sefaria.org")