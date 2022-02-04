import django
django.setup()
from sefaria.model import *
import csv
with open("English Version Titles - version_titles.csv", 'r') as f:
    rows = list(csv.reader(f))[1:]
    for row in rows:
        print(row)
        vs = VersionSet({"versionTitle": row[0]})
        print(abs(vs.count() - int(row[1])))
        if len(row[2]) > 0:
            for v in vs:
                v.shortVersionTitle = row[2]
                v.save(override_dependencies=True)


from sefaria.helper.schema import *
parent_node = library.get_index("The Five Books of Moses, by Everett Fox").nodes
intro = "הקדמה "
parts = ["א", "ב", "ג", "ד"]
preface = JaggedArrayNode()
preface.add_primary_titles("Translator's Preface", intro+parts[0])
preface.add_structure(["Paragraph"])
preface.validate()
name = JaggedArrayNode()
name.add_primary_titles("On the Name of God and Its Translation", intro+parts[1])
name.add_structure(["Paragraph"])
name.validate()
guide = JaggedArrayNode()
guide.add_primary_titles("Guide to the Pronunciation of Hebrew Names", intro+parts[2])
guide.add_structure(["Paragraph"])
guide.validate()
aid = JaggedArrayNode()
aid.add_primary_titles("To Aid the Reader of Genesis and Exodus", intro+parts[3])
aid.add_structure(["Paragraph"])
aid.validate()

insert_first_child(aid, parent_node)

parent_node = library.get_index("The Five Books of Moses, by Everett Fox").nodes
insert_first_child(guide, parent_node)

parent_node = library.get_index("The Five Books of Moses, by Everett Fox").nodes
insert_first_child(name, parent_node)

parent_node = library.get_index("The Five Books of Moses, by Everett Fox").nodes
insert_first_child(preface, parent_node)
