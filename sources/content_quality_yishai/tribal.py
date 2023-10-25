import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import attach_branch

root = library.get_index('Tribal Lands').nodes
new = JaggedArrayNode()
new.add_primary_titles('Chapter 15; Binyamin', 'טו; בנימין')
new.depth = 1
new.addressTypes = ["Integer"]
new.sectionNames = ["Paragraph"]
new.validate()
attach_branch(new, root, 17)

