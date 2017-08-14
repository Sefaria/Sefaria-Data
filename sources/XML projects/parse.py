# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach

SERVER = "http://draft.sefaria.org"

def create_schema(en_title, he_title, categories):
    root = SchemaNode()
    root.add_primary_titles(en_title, he_title)
    nodes_arr = """Preface
Use of a Prosthetic Device
A Divorce by An Insane Man
Circumcisions Overseas in the Absence of a Mohel
Circumcising a Child of a Mixed Marriage
Use of "The Lord's Prayer"
Burial of Two Coffins in the Same Grave
Burial of Stillborn Infants
Volunteering For the Military Chaplaincy
Photographed Torah Scrolls
Use of Bone Fragments in Bone Surgery
Brain Surgery, Lobotomy"""
    nodes_arr = nodes_arr.split("\n")

    for count, en in enumerate(nodes_arr):
        node = JaggedArrayNode()
        node.add_structure(["Paragraph"])
        heb = numToHeb(count+1)
        node.add_primary_titles(en, heb)
        node.validate()
        root.append(node)

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
    library.rebuild()
    add_term("Preface", u"פתח דבר", "pseudo_toc_categories", SERVER)
    create_schema("Responsa to Chaplains", u"פ", ["Halakhah"])
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Responsa to Chaplains"
    post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002109525"
    title = "Responsa to Chaplains"
    file_name = "Responsa_to_Chaplains.xml"

    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                titled=True)
    parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify)
    parser.run()

