import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import attach_branch

parent_node = Ref("Machzor Vitry").index_node
new_node = JaggedArrayNode()
new_node.add_primary_titles('Seder Kriat Shema Al HaMitah', 'סדר קריאת שמע על המיטה')
new_node.add_structure(['Siman', "Paragraph"])
new_node.validate()
attach_branch(new_node, parent_node, 4)

vtitle = 'Machzor Vitry, Berlin, 1893-97'

pitum_tc = Ref("Machzor Vitry, Pitum HaKetoret").text('he', vtitle)
pitum_text = pitum_tc.text
kriat_text = pitum_text[:]

pitum_text = pitum_text[:-1]
pitum_tc.text = pitum_text
pitum_tc.save()

kriat_tc = Ref("Machzor Vitry, Seder Kriat Shema Al HaMitah").text('he', vtitle)
kriat_text[-2] = []
kriat_tc.text = kriat_text
kriat_tc.save()
