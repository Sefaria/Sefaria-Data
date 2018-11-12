# -*- coding: utf-8 -*-

from sefaria.model import *
from sefaria.helper.schema import insert_first_child, convert_simple_index_to_complex, insert_last_child

i = library.get_index("Likutei Moharan")
convert_simple_index_to_complex(i)

i = library.get_index("Likutei Moharan")
root = i.nodes

hakdama = JaggedArrayNode()
shir = JaggedArrayNode()
lechu = JaggedArrayNode()
tinyana = JaggedArrayNode()
letters = JaggedArrayNode()

hakdama.key = "Introduction"
hakdama.add_title("Introduction", "en", primary=True)
hakdama.add_title(u"הקדמה", "he", primary=True)
hakdama.depth = 1
hakdama.sectionNames = ["Paragraph"]
hakdama.addressTypes = ["Integer"]

shir.key = "Shir"
shir.add_title("A Pleasant Song", "en", primary=True)
shir.add_title(u"שיר נעים", "he", primary=True)
shir.depth = 1
shir.sectionNames = ["Line"]
shir.addressTypes = ["Integer"]

lechu.key = "Lechu"
lechu.add_title("Go See", "en", primary=True)
lechu.add_title(u"לכו חזו", "he", primary=True)
lechu.depth = 1
lechu.sectionNames = ["Paragraph"]
lechu.addressTypes = ["Integer"]

tinyana.key = "Tinyana"
tinyana.add_title("Part II", "en", primary=True)
tinyana.add_title("Tinyana", "en")
tinyana.add_title(u"תנינא", "he", primary=True)
tinyana.depth = 2
tinyana.sectionNames = ["Torah", "Section"]
tinyana.addressTypes = ["Integer", "Integer"]

letters.key = "Letters"
letters.add_title("Letters", "en", primary=True)
letters.add_title(u"מכתבים", "he", primary=True)
letters.depth = 2
letters.sectionNames = ["Letter", "Paragraph"]
letters.addressTypes = ["Integer", "Integer"]

insert_first_child(lechu, root)
insert_first_child(shir, root)
insert_first_child(hakdama, root)
insert_last_child(tinyana, root)
insert_last_child(letters, root)

