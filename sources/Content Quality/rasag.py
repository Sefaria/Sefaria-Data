#encoding=utf-8
from sefaria.model import *
from sources.functions import *

root = SchemaNode()
root.add_primary_titles("Sefer Hamitzvot of Rasag", u"ספר המצוות")
root.key = "seferhamitzvotrasag"
pos = JaggedArrayNode()
pos.add_primary_titles("Positive Commandments", u"מצות עשה")
pos.depth = 1
pos.add_structure(["Comment"])
pos.validate()
root.append(pos)
other_nodes = [("Negative Commandments", u"מצות לא תעשה"), ("Communal Laws", u"עונשים"), ("Laws of the Court", u"פרשיות ציבור")]
for titles in other_nodes:
    neg = SchemaNode()
    neg.key = titles[0]
    neg.add_primary_titles(titles[0], titles[1])
    neg.append(create_intro())
    neg.validate()
    neg_d = JaggedArrayNode()
    neg_d.depth = 1
    neg_d.default = True
    neg_d.key = "default"
    neg_d.add_structure("Comment")
    neg_d.validate()
    neg.append(neg_d)
    neg.validate()
    root.append(neg)
root.validate()
index = {
    "title": "Sefer Hamitzvot of Rasag",
    "schema": root.serialize(),
    "categories": ["Halakhah"]
}
post_index(index, "http://localhost:8000")