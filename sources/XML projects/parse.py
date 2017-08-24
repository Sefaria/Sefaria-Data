# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach

SERVER = "http://ste.sefaria.org"

def create_schema(en_title, he_title, categories):
    root = SchemaNode()
    root.add_primary_titles(en_title, he_title)
    nodes_arr = """USE OF A PROSTHETIC DEVICE
BRAIN SURGERY: LOBOTOMY
BURIAL OF STILLBORN INFANTS
BURIAL OF TWO COFFINS IN THE SAME GRAVE
A DIVORCE BY AN INSANE MAN
VOLUNTEERING FOR THE MILITARY CHAPLAINCY
USE OF "THE LORD'S PRAYER"
PHOTOGRAPHED TORAH SCROLLS
CIRCUMCISING A CHILD OF A MIXED MARRIAGE
CIRCUMCISIONS OVERSEAS IN THE ABSENCE OF A MOHEL
USE OF BONE FRAGMENTS IN BONE SURGERY"""
    nodes_heb_arr = """שימוש בתותב
גירושין על ידי שוטה
עריכת ברית בהעדר מוהל
עריכת ברית לנולד מנישואי תערובת
שימוש בקטע תפילה נוצרית
קבורת שני מתים בקבר אחד
קבורת נפל
התגייסות לתפקיד קצונה דתית
דין ספר תורה שהועתק במכונת צילום
שימוש בשברי עצם עבור ניתוח אורתופדי
ניתוח מח, לובוטומיה"""
    nodes_arr = nodes_arr.split("\n")
    nodes_heb_arr = nodes_heb_arr.split("\n")
    assert len(nodes_arr) == len(nodes_heb_arr)


    preface = JaggedArrayNode()
    preface.add_shared_term("Preface")
    preface.key = 'preface'
    preface.add_structure(["Paragraph"])
    root.append(preface)

    for count, en in enumerate(nodes_arr):
        en = en.lower()
        node = JaggedArrayNode()
        node.add_structure(["Paragraph"])
        node.add_primary_titles(en, nodes_heb_arr[count])
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
    add_term("Preface", u"פתח דבר", "pseudo_toc_categories", "http://localhost:8000")
    create_schema("Responsa to Chaplains", u"משהו", ["Halakhah"])
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

