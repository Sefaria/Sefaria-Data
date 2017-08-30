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
    nodes_arr = """Introduction
Cohen and Conscientious Objectors
Mikvah
Minyan At Brith
Pidyon Haben
Wearing a Cross
Dietary Laws; Violation
Sabbath Observers; Exemptions
Sabbath in the Far East and Its Relationship to the International Date Line,
Advancing the Hour of Friday Evening Services
Friday Evening Service in Artic Regions
Religious Services and Christmas Decorations
Head Covering and the National Anthem
Use of the Sefer Torah
Haftarah on Friday Night
Marriage
Conversions
Performance of Marriage of Protestant Girl to Jewish Lieutenant; Conversion
Forms of the Marriage Ceremony
Marriage Ceremony Friday Night
Marriages by Radio Telephone
Marriage Without Previous Divorce (Get)
Emergency Mixed Marriage
Divorce
Remarriage and Jewish Divorce
Kethubbah
K'riah
The Burial of the Blood Removed From the Body During Embalming
Dress of Military Dead
Use of the Tallith in Military Burial
Talleithim For the Dead
Use of the Tallith in Military Burial
Position of Individual Officiating At Grave
Position of Coffin During Service
Decoration of Jewish Military Graves
Kaddish
Communal Recitation of Kaddish
Yahrzeit
Yahrzeit; Which Day is to Be Observed When Date of Death is Unknown
Burial on Sabbath
Disinterment
May a Body Being Removed From a Temporary to a Permanent Coffin Be Then Draped With a Tallith
Jewish Funeral Escorts
Cremation of Amputated Portions of the Body
Autopsy
Burial of Ashes of Cremated Soldiers
Washing of Bodies and Bronze Caskets
Burial in National Cemeteries
Ritual of Mourning For Reinterment"""
    nodes_arr = nodes_arr.split("\n")
    nodes_heb_arr = []
    for count, node in enumerate(nodes_arr):
        nodes_heb_arr.append(u"חלק"+numToHeb(count+1))
    assert len(nodes_arr) == len(nodes_heb_arr)


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

if __name__ == "__main__":
    #add_term("Preface", u"פתח דבר", "pseudo_toc_categories", "http://localhost:8000")
    create_schema("Responsa in Wartime", u"הו", ["Halakhah"])
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Responsa in Wartime"
    post_info["versionSource"] = "http://primo.nli.org.il/"
    title = "Responsa in Wartime"
    file_name = "ResponsaInWartime.xml"

    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                titled=True)
    parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify)
    parser.run()

