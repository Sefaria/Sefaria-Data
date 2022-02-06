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
parent = library.get_index("The Five Books of Moses, by Everett Fox")
vayikra_node = parent.nodes.children[-4].children[-3]
vayikra_pos = 3
title = "ויקרא הערה ב׳ א"
new = JaggedArrayNode()
new.add_primary_titles("Pollution from Tzaraat", title)
new.add_structure(["Paragraph"])
attach_branch(new, vayikra_node, vayikra_pos)

parent = library.get_index("The Five Books of Moses, by Everett Fox")
numbers_node = parent.nodes.children[-3].children[2]
numbers_pos = 12
new = JaggedArrayNode()
title = 'במדבר הערה י״א ב'
new.add_structure(["Paragraph"])
new.add_primary_titles("On Bil'am", title)
attach_branch(new, numbers_node, numbers_pos)

parent_node = library.get_index("The Five Books of Moses, by Everett Fox").nodes
intro = "הקדמה "
parts = ["א", "ב", "ג", "ד", "ה"]
preface = JaggedArrayNode()
preface.add_primary_titles("Translator's Preface", intro+parts[0])
preface.add_structure(["Paragraph"])
preface.validate()
ack = JaggedArrayNode()
ack.add_primary_titles("Acknowledgements", intro+parts[1])
ack.add_structure(["Paragraph"])
ack.validate()
name = JaggedArrayNode()
name.add_primary_titles("On the Name of God and Its Translation", intro+parts[2])
name.add_structure(["Paragraph"])
name.validate()
guide = JaggedArrayNode()
guide.add_primary_titles("Guide to the Pronunciation of Hebrew Names", intro+parts[3])
guide.add_structure(["Paragraph"])
guide.validate()
aid = JaggedArrayNode()
aid.add_primary_titles("To Aid the Reader of Genesis and Exodus", intro+parts[4])
aid.add_structure(["Paragraph"])
aid.validate()

sugg = JaggedArrayNode()
sugg.add_primary_titles("Suggestions for Further Reading", "המלצות לקריאה נוספת")
sugg.add_structure(["Paragraph"])
sugg.validate()

insert_first_child(aid, parent_node)

parent_node = library.get_index("The Five Books of Moses, by Everett Fox").nodes
insert_first_child(guide, parent_node)

parent_node = library.get_index("The Five Books of Moses, by Everett Fox").nodes
insert_first_child(name, parent_node)

parent_node = library.get_index("The Five Books of Moses, by Everett Fox").nodes
insert_first_child(ack, parent_node)

parent_node = library.get_index("The Five Books of Moses, by Everett Fox").nodes
insert_first_child(preface, parent_node)
parent_node = library.get_index("The Five Books of Moses, by Everett Fox").nodes

insert_last_child(sugg, parent_node)


vtitle = "The Five Books of Moses, by Everett Fox. New York, Schocken Books, 1995"
everett = ["The Five Books of Moses, by Everett Fox, Leviticus, Part II; Ritual Pollution and Purification, Pollution from Tzaraat 2-4",
"The Five Books of Moses, by Everett Fox, Numbers, Part II; The Rebellion Narratives, On Bil'am 2-10"]
tanakh_refs = ["Leviticus 13", "Numbers 22:5-25:9"]
for refs in zip(tanakh_refs, everett):
	e, t = refs
	Link({"refs": [t, e],
                                       "auto": True, "type": "essay", "generated_by": "everett_fox_essay_links",
                                       "versions": [{"title": vtitle,
                                                     "language": "en"},
                                                    {"title": vtitle,
                                                     "language": "en"}],
                                       "displayedText": [{"en": t, "he": Ref(t).he_normal()},
                                                         {"en": e.replace(':', ';'), "he": Ref(e).he_normal()}]}).save()