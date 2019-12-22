#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *
# he_title = u"חבצלת השרון"
# en_title = "Chavatzelet HaSharon"
# versionSource = "https://dlib.rsl.ru/viewer/01007486988#?page=1"
# versionTitle = "{}, Warsaw 1876".format(en_title)
# root = SchemaNode()
# root.add_primary_titles("{} on Daniel".format(en_title), u"{} על דנואל".format(he_title))
# intro = JaggedArrayNode()
# intro.add_primary_titles("Introduction", u"הקדמת המבחר")
# intro.add_structure(["Paragraph"])
# intro.key = "Introduction"
# preface = JaggedArrayNode()
# preface.add_primary_titles("Preface", u"הקדמת הספר")
# preface.key = "Preface"
# preface.add_structure(["Paragraph"])
# default = JaggedArrayNode()
# default.key = "default"
# default.default = True
# default.add_structure(["Chapter", "Verse", "Paragraph"])
# root.append(intro)
# root.append(preface)
# root.append(default)
# root.validate()
# post_index({"title": "{} on Daniel".format(en_title),
#             "dependence": "Commentary", "collective_title": "Alshich",
#             "categories": ["Tanakh", "Commentary", "Alshich", "Writings"], "schema": root.serialize()})

he_title, en_title = """רב פנינים על משלי / Rav Peninim on Proverbs""".split(" / ")
root = SchemaNode()
root.add_primary_titles(en_title, he_title)
intro = JaggedArrayNode()
intro.add_shared_term("Introduction")
intro.add_structure(["Paragraph"])
intro.key = "Introduction"
default = JaggedArrayNode()
default.default = True
default.key = "default"
default.add_structure(["Chapter", "Verse", "Comment"])
root.append(intro)
root.append(default)
root.validate()
post_index({"title": en_title,
            "base_text_titles": ["Proverbs"],
            "base_text_mapping": "many_to_one_default_only",
            "dependence": "Commentary", "collective_title": "Alshich",
            "categories": ["Tanakh", "Commentary", "Alshich", "Writings"], "schema": root.serialize()})