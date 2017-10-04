# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from sefaria.model.category import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach
import num2words

SERVER = "http://draft.sefaria.org"

def create_schema(en_title, he_title, categories, parser):
    root = SchemaNode()
    root.add_primary_titles(en_title, he_title)

    node = JaggedArrayNode()
    node.add_structure(["Paragraph"])
    node.add_shared_term("Introduction")
    node.key = "intro"
    root.append(node)

    with open("en_to_he.csv") as file:
        reader = UnicodeReader(file)
        for row in reader:
            assert len(row) is 2
            en, he = row[0], row[1]
            if en == "English Chapter Names":
                continue
            en = parser.cleanNodeName(en)
            new_node = JaggedArrayNode()
            new_node.add_primary_titles(en, he)
            new_node.add_structure(["Paragraph"])
            root.append(new_node)

    root.validate()
    index = {
        "schema": root.serialize(),
        "title": en_title,
        "categories": categories,
    }
    post_index(index, server=SERVER)


def reorder_modify(text):
    return bleach.clean(text, strip=True)


if __name__ == "__main__":
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Or Hachayim, trans. Eliyahu Munk, 1998"
    post_info["versionSource"] = "http://www.urimpublications.com/Merchant2/merchant.mv?Screen=PROD&Store_Code=UP&Product_Code=or"
    title = "Or HaChaim"
    torah_books = library.get_indexes_in_category("Torah")
    for i in range(5):
        this_book = "Or HaChaim on {}".format(torah_books[i])
        parser = XML_to_JaggedArray(this_book, "OhrHachaim-Vol{}.xml".format(i+1), allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                    titled=True)
        #create_schema("Ohr HaChaim Vol {}".format(num2words(i+1)), u"אור החיים", ["Tanakh", "Commentary", "Ohr HaChaim"], parser)
        parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify)
        results = parser.run()
