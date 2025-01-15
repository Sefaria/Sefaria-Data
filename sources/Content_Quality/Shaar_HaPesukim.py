import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import attach_branch, reorder_children

parent_node = Ref("Sha'ar HaPesukim").index_node

news = [('Book of Samuel II', 'ספר שמואל ב'), ('Book of Samuel I', 'ספר שמואל א')]
for i in range(2):
    new_node = JaggedArrayNode()
    new_node.add_primary_titles(*news[i])
    new_node.add_structure(["Paragraph"])
    new_node.validate()
    attach_branch(new_node, parent_node, 54)
keys = [n.key for n in parent_node.children]
new = keys[:54] + [keys[56]] + keys[54:56] + keys[57:]
reorder_children(parent_node, new)
