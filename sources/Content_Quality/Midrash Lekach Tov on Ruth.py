from sefaria.model import *
from sefaria.helper.schema import *
t = Term()
t.name = "Midrash Lekach Tov"
t.add_primary_titles("Midrash Lekach Tov", u"מדרש לקח טוב")
t.save()

index = library.get_index("Midrash Lekach Tov on Ruth")
index.dependence = "Commentary"
index.base_text_titles = ["Ruth"]
index.base_text_mapping = "many_to_one"
index.collective_title = "Midrash Lekach Tov"
index.categories = ["Midrash", "Aggadic Midrash"]
index.save()
convert_simple_index_to_complex(index)

index = library.get_index("Midrash Lekach Tov on Ruth")
parent = index.nodes
intro = JaggedArrayNode()
intro.add_shared_term("Introduction")
intro.add_structure(["Paragraph"])
intro.key = "intro"
attach_branch(intro, parent)


