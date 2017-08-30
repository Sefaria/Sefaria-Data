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
    nodes_arr = """Use of a Prosthetic Device
Brain Surgery; Lobotomy
Burial of Stillborn Infants
Burial of Two Coffins in the Same Grave
A Divorce by An Insane Man
Volunteering For the Military Chaplaincy
Use of "The Lord's Prayer"
Photographed Torah Scrolls
Circumcising a Child of a Mixed Marriage
Circumcisions Overseas in the Absence of a Mohel
Use of Bone Fragments in Bone Surgery"""
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
        print en
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


def get_dict_of_names(file):
    import csv
    reader = csv.reader(open(file))
    dict = {}
    for row in reader:
        dict[row[0]] = row[1]
    return dict


if __name__ == "__main__":
    #add_term("Preface", u"פתח דבר", "pseudo_toc_categories", "http://localhost:8000")
    #create_schema("Responsa to Chaplains", u"משהו", ["Halakhah"])
    dict_of_names = get_dict_of_names("Birnbaum Misheh Torah - Sheet1.csv")
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix", "h1"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Maimonides' Mishneh Torah, edited by Philip Birnbaum, New York, 1967"
    post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002108864"
    title = "Mishneh Torah"
    file_name = "MishnehTorah_Abridged_Birnbaum.xml"

    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                titled=True, dict_of_names=dict_of_names)
    parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify)
    parser.run()

