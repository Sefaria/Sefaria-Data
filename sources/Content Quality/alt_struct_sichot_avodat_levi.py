from sefaria.model import *
from bs4 import BeautifulSoup
file = open("alt_struct_sichot_avodat_levi.xml")
soup = BeautifulSoup(file)
elements = [el for el in soup.find("opml").contents[3:] if el != "\n"]
for el in elements:
    parsha_he, parsha_en = el.attrs["text"].split(" / ")
    parsha_node = SchemaNode()
    parsha_node.add_primary_titles(parsha_en, parsha_he)
    for child in [child for child in el.contents if child != "\n"]:
        he, en = el.attrs["text"].split(" / ")
        child_node = ArrayMapNode()
        child_node.add_primary_titles(en, he)
        

