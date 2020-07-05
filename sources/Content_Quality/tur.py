#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *
import os
import csv
class Node:
    def __init__(self, en_section, he_topic, en_topic, start):
        self.en_section = en_section
        self.en_topic = en_topic
        self.he_topic = he_topic
        self.start = int(start)
        self.end = -1

    def get_range(self):
        assert self.start <= self.end
        return "{}-{}".format(self.start, self.end)

    def convertToArrayMapNode(self):
        arrayMapNode = ArrayMapNode()
        arrayMapNode.add_primary_titles(self.en_topic, self.he_topic)
        arrayMapNode.depth = 0
        arrayMapNode.refs = ""
        arrayMapNode.wholeRef = "{} {}".format(self.en_section, self.get_range())
        arrayMapNode.includeSections = True
        arrayMapNode.validate()
        return arrayMapNode.serialize()



# #
from sefaria.helper.schema import change_node_title
title = "Tur"
print title
print "Changing node titles"
index = library.get_index(title)
parent = index.nodes
#change_node_title(parent.children[1], "Yoreh Deah", "en", "Yrh Dh")
change_node_title(parent.children[1], u"יורה דעה", "he", u"יורה דאה")
#
# library.rebuild(include_toc=True)
# for title in ["Tur", "Beit Yosef"]:
#     print title
#     print "Adding intro"
#     intro = JaggedArrayNode()
#     intro.add_shared_term("Introduction")
#     intro.key = "Introduction"
#     intro.add_structure(["Paragraph"])
#     index = library.get_index(title)  # reloading index to ensure we have the most up-to-date in memory
#     parent = index.nodes
#     insert_first_child(intro, parent)

    # links = []
    # for sec_ref in library.get_index("Tur").all_section_refs():
    #     tur_ref = sec_ref.as_ranged_segment_ref().normal()
    #     shulchan_str = sec_ref.normal().replace("Tur", "Shulchan Arukh").replace("Chaim", "Chayim").replace("Deah", "De'ah")
    #     shulchan_str += ":1"
    #     link = {"refs": [tur_ref, shulchan_str], "auto": True, "type": "Commentary",
    #             "generated_by": "tur_content_quality"}
    #     assert Ref(shulchan_str)
    #     links.append(link)
    # post_link(links, server="https://www.sefaria.org", VERBOSE=True)



#
# files = [f for f in os.listdir("./Tur Alt Struct") if f.endswith(".csv")]
# big_four = []
# title = "Tur"
#
# for file in files:
#     nodes = []
#     en_section = "{}, {}".format(title, file[0:-4])
#     index = library.get_index(file[0:-4])
#     section_en, section_he = index.get_title('en').split(", ")[-1], index.get_title('he')
#     titles = [{"lang": "he", "text": section_he, "primary": True},
#               {"lang": "en", "text": section_en, "primary": True}]
#     with open("./Tur Alt Struct/"+file) as f:
#         reader = csv.reader(f)
#         for row in reader:
#             print row
#             node = Node(en_section, row[0], row[1], row[2])
#             if nodes:
#                 nodes[-1].end = max(node.start - 1, nodes[-1].start) #nodes[-1].start -> for the case where two in a row have same start
#             nodes.append(node)
#         last_page = Ref(en_section).all_segment_refs()[-1].sections[0]
#         nodes[-1].end = last_page
#         for i, node in enumerate(nodes):
#             nodes[i] = nodes[i].convertToArrayMapNode()
#             #nodes[i]["wholeRef"] = nodes[i]["wholeRef"].replace("Chaim", "Chayim").replace("Deah", "De'ah")
#     big_four.append({"nodes": nodes, "titles": titles})
#
#
# index = get_index_api(title, server="http://www.sefaria.org")
# big_four = [big_four[1], big_four[-1], big_four[0], big_four[2]]
# index["alt_structs"] = {"Topic": {"nodes": big_four}}
# post_index(index, server="https://www.sefaria.org")
#
