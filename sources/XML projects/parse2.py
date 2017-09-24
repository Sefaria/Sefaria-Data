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




def change_priority(dict_of_names):
    pass




if __name__ == "__main__":
    arr = [u'Mishneh Torah, Transmission of the Oral Law',
 u'Mishneh Torah, Foundations of the Torah',
 u'Mishneh Torah, Human Dispositions',
 u'Mishneh Torah, Torah Study',
 u'Mishneh Torah, Foreign Worship and Customs of the Nations',
 u'Mishneh Torah, Repentance',
 u'Mishneh Torah, Reading the Shema',
 u'Mishneh Torah, Prayer and the Priestly Blessing',
 u'Mishneh Torah, Tefillin, Mezuzah and the Torah Scroll',
 u'Mishneh Torah, Fringes',
 u'Mishneh Torah, Blessings',
 u'Mishneh Torah, Sabbath',
 u'Mishneh Torah, Eruvin',
 u'Mishneh Torah, Rest on the Tenth of Tishrei',
 u'Mishneh Torah, Rest on a Holiday',
 u'Mishneh Torah, Leavened and Unleavened Bread',
 u'Mishneh Torah, Shofar, Sukkah and Lulav',
 u'Mishneh Torah, Sheqel Dues',
 u'Mishneh Torah, Sanctification of the New Month',
 u'Mishneh Torah, Fasts',
 u'Mishneh Torah, Scroll of Esther and Hanukkah',
 u'Mishneh Torah, Marriage',
 u'Mishneh Torah, Divorce',
 u'Mishneh Torah, Levirate Marriage and Release',
 u'Mishneh Torah, Forbidden Foods',
 u'Mishneh Torah, Ritual Slaughter',
 u'Mishneh Torah, Oaths',
 u'Mishneh Torah, Vows',
 u'Mishneh Torah, Nazariteship',
 u'Mishneh Torah, Gifts to the Poor',
 u'Mishneh Torah, Heave Offerings',
 u'Mishneh Torah, Tithes',
 u'Mishneh Torah, First Fruits and other Gifts to Priests Outside the Sanctuary',
 u'Mishneh Torah, Sabbatical Year and the Jubilee',
 u'Mishneh Torah, The Chosen Temple',
 u'Mishneh Torah, Vessels of the Sanctuary and Those who Serve Therein',
 u'Mishneh Torah, Daily Offerings and Additional Offerings',
 u'Mishneh Torah, Trespass',
 u'Mishneh Torah, Festival Offering',
 u'Mishneh Torah, Firstlings',
 u'Mishneh Torah, Defilement by a Corpse',
 u'Mishneh Torah, Defilement by Leprosy',
 u'Mishneh Torah, Defilement of Foods',
 u'Mishneh Torah, Immersion Pools',
 u'Mishneh Torah, Damages to Property',
 u'Mishneh Torah, Theft',
 u'Mishneh Torah, Robbery and Lost Property',
 u'Mishneh Torah, One Who Injures a Person or Property',
 u'Mishneh Torah, Murderer and the Preservation of Life',
 u'Mishneh Torah, Sales',
 u'Mishneh Torah, Ownerless Property and Gifts',
 u'Mishneh Torah, Neighbors',
 u'Mishneh Torah, Agents and Partners',
 u'Mishneh Torah, Slaves',
 u'Mishneh Torah, Hiring',
 u'Mishneh Torah, Borrowing and Deposit',
 u'Mishneh Torah, Creditor and Debtor',
 u'Mishneh Torah, Plaintiff and Defendant',
 u'Mishneh Torah, Inheritances',
 u'Mishneh Torah, The Sanhedrin and the Penalties within their Jurisdiction',
 u'Mishneh Torah, Testimony',
 u'Mishneh Torah, Rebels',
 u'Mishneh Torah, Mourning',
 u'Mishneh Torah, Kings and Wars']
    start = "Neighbors"
    dont_start = True
    for book in arr:
        if start not in book and dont_start:
            continue
        else:
            dont_start = False

        get_rid_of_numbers(book, "Maimonides' Mishneh Torah, edited by Philip Birnbaum, New York, 1967",
                           "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002108864",
                           SERVER, SERVER)


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
    change_priority(dict_of_names)


    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                titled=True, dict_of_names=dict_of_names)
    parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify)
    parser.run()


versionTitle = "Maimonides' Mishneh Torah, edited by Philip Birnbaum, New York, 1967"
for book in library.get_indexes_in_category("Mishneh Torah"):
    book = library.get_index(book)
    vs = book.versionSet()
    for v in vs:
        if v.versionTitle == versionTitle:
            print book.title
            assert v.priority == 1.0
            assert v.digitizedBySefaria == True
            v.status = "locked"
            v.save()
