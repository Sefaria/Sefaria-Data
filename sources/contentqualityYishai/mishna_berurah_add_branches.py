import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import convert_simple_index_to_complex, attach_branch

index = library.get_index('Mishnah Berurah')
convert_simple_index_to_complex(index)
index = library.get_index('Mishnah Berurah')
parent = index.nodes
titles = [['Introduction to the Laws of Shabbat', 'הקדמה להלכות שבת'],
        ['Introduction', 'הקדמה']]
for n in range(2):
    node = JaggedArrayNode()
    node.add_primary_titles(*titles[n])
    node.add_structure(['Paragraph'])
    node.serialize()
    attach_branch(node, parent)
