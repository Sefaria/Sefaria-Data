import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import *
from collections import defaultdict
#def attach_branch(new_node, parent_node, place=0):


#
#
# new_node = JaggedArrayNode()
# new_node.add_structure(["Chapter", "Verse"])
# new_node.add_shared_term("Vayetzei")
# new_node.key = "Vayetzei"
# book = library.get_index("Penei David")
# parent_node = book.nodes.children[1]
# place = 5
# attach_branch(new_node, parent_node, place=place)
# library.rebuild(include_toc=True)
#
# new_node = JaggedArrayNode()
# new_node.add_structure(["Chapter", "Verse"])
# new_node.add_shared_term("Toldot")
# new_node.key = "Toldot"
# book = library.get_index("Penei David")
# parent_node = book.nodes.children[1]
# attach_branch(new_node, parent_node, place=place)

refs = Ref("Penei David, Genesis, Chayei Sara").all_segment_refs()
sections = defaultdict(int)
for r in refs[87:]:
    sections[r.section_ref().normal()] += 1
    new_ref = f"Penei David, Genesis, Vayetzei {len(sections)}:{sections[r.section_ref().normal()]}"
    new_tc = TextChunk(Ref(new_ref), lang='he', vtitle="Penei David -- Torat Emet")
    old_tc = TextChunk(r, lang='he', vtitle="Penei David -- Torat Emet")
    new_tc.text = old_tc.text
    new_tc.save()
    old_tc.text = ""
    old_tc.save()

