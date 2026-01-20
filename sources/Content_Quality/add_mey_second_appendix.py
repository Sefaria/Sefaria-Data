import django

django.setup()

from sefaria.model import *
from sefaria.helper.schema import attach_branch

# Load the Mishnat Eretz Yisrael on Mishnah Megillah index / parent node
mey_idx = Index().load({'title': 'Mishnat Eretz Yisrael on Mishnah Megillah'})
parent_node_mey = mey_idx.nodes

# Create new node for "Appendix 2"
new_node = JaggedArrayNode()
new_node.key = "Appendix 2"
new_node.add_structure(["Paragraph"])
new_node.add_primary_titles(en_title="Appendix 2", he_title="נספח ב")
new_node.validate()

# Add new node to correct position
attach_branch(new_node=new_node, parent_node=parent_node_mey, place=3)

# Confirm via reload
mey_idx = Index().load({'title': 'Mishnat Eretz Yisrael on Mishnah Megillah'})
print(mey_idx.nodes.children)

