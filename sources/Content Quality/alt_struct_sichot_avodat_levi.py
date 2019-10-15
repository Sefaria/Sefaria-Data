import django
django.setup()
from sefaria.model import *
from bs4 import BeautifulSoup
from sources.functions import get_index_api, post_index
file = open("alt_struct_sichot_avodat_levi.xml")
soup = BeautifulSoup(file)
nodes = []
index = get_index_api("Sichot Avodat Levi", server="http://draft.sefaria.org")
elements = [el for el in soup.find("opml").contents[3:] if el != "\n"]
for el in elements:
    parsha_he, parsha_en = el.attrs["text"].split(" / ")
    parsha_node = SchemaNode()
    parsha_node.add_primary_titles(parsha_en, parsha_he)
    for child in [child for child in el.contents if child != "\n"]:
        he, en = child.attrs["text"].split(" / ")
        ref = en.replace("Section ", "")
        child_node = ArrayMapNode()
        child_node.add_primary_titles(en, he)
        child_node.depth = 0
        child_node.refs = []
        child_node.wholeRef = "Sichot Avodat Levi {}".format(ref)
        parsha_node.append(child_node)
    parsha_node.validate()
    nodes.append(parsha_node.serialize())
index["alt_structs"] = {"Parasha": {"nodes": nodes}}
post_index(index, server="http://draft.sefaria.org")

