# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import sys
import re
from sefaria.model import *
from XML_to_JaggedArray_new import XML_to_JaggedArray

def create_schema(en_parshiot, he_parshiot):
    book = SchemaNode()
    book.add_title("Buber Midrash Tanchuma", "en", primary=True)
    book.add_title(u"תנחומא - בובר", "he", primary=True)
    book.key = "buber_midrash_tanhuma"
    '''
    cycle through each one, at the beginning of each one add foreword and preface, then add as many parshiot and keep track
    '''
    prev = 0
    for vol_info in [(12, "One"), (21, "Two"), (21, "Three")]:
        volume = SchemaNode()
        vol_length = vol_info[0]
        vol_name = vol_info[1]
        volume.add_title("Volume {}".format(vol_name), "en", primary=True)
        volume.add_title(u"שער", "he", primary=True)
        volume.key = vol_info[1]
        foreword = JaggedArrayNode()
        foreword.key = "foreword"+str(vol_length)
        foreword.add_title("Foreword", "en", primary=True)
        foreword.add_title(u"פתח דבר", "he", primary=True)
        foreword.depth = 1
        foreword.addressTypes = ["Integer"]
        foreword.sectionNames = ["Paragraph"]
        preface = JaggedArrayNode()
        preface.key = "preface"+str(vol_length)
        preface.add_title("Preface", "en", primary=True)
        preface.add_title(u"הקדמה", "he", primary=True)
        preface.depth = 1
        preface.addressTypes = ["Integer"]
        preface.sectionNames = ["Paragraph"]
        volume.append(foreword)
        volume.append(preface)
        for count in range(vol_length):
            parsha = JaggedArrayNode()
            en_parsha = en_parshiot[count + prev]
            parsha.key = en_parsha
            parsha.add_title(en_parsha, "en", primary=True)
            parsha.add_title(he_parshiot[count + prev], "he", primary=True)
            parsha.sectionNames = ["Paragraph"]
            parsha.depth = 1
            parsha.addressTypes = ["Integer"]
            volume.append(parsha)
        book.append(volume)
        prev += vol_length

    book.validate()
    index = {
        "schema": book.serialize(),
        "title": "Midrash Tanchuma Buber",
        "categories": ["Midrash", "Midrash Tanchuma"]
    }
    post_index(index)



def parse(text_arr):
    assert type(text_arr) is list
    for index, text in enumerate(text_arr):
        text_arr[index] = text_arr[index].replace("<bold>", "<b>").replace("<italic>", "<i>").replace("</bold>", "</b>").replace("</italic>", "</i>")
        xref_start = re.findall("<xref.*?>", text_arr[index])
        xref_end = re.findall("</xref.*?>", text_arr[index])
        xrefs = xref_start + xref_end
        for xref in xrefs:
            text_arr[index] = text_arr[index].replace(xref, "")

    return text_arr


if __name__ == "__main__":
    import csv
    en_parshiot = []
    he_parshiot = []
    with open("../../../Sefaria-Project/data/tmp/parsha.csv") as parsha_file:
        parshiot = csv.reader(parsha_file)
        parshiot.next()
        order = 1
        for row in parshiot:
            (en, he, ref) = row
            if en == "Lech-Lecha":
                en = "Lech Lecha"
            he = he.decode('utf-8')
            en_parshiot.append(en)
            he_parshiot.append(he)
    post_info = {}
    post_info["versionTitle"] = "Midrash Tanhuma-Yelammedenu, trans. Samuel A. Berman"
    post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001350458"
    post_info["language"] = "en"
    post_info["server"] = sys.argv[2]
    allowed_tags = ["book", "volume", "intro", "foreword", "part", "chapter", "p", "ftnote", "title"]
    allowed_attributes = ["id"]
    if sys.argv[1] == "Buber":
        file_name = "buber.xml"
        titles = ["Midrash Tanchuma Buber, Volume One", "Midrash Tanchuma Buber, Volume Two", "Midrash Tanchuma Buber, Volume Three"]
        create_schema(en_parshiot, he_parshiot)
        for title in titles:
            tanhuma = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, en_parshiot)
            grab_title_lambda = lambda x: x[0].tag == "title"
            p = re.compile("\d+\.")
            reorder_test_lambda = lambda x: x.tag != "ftnote" and p.match(x.text) is not None
            def reorder_modify(text):
                return text.split(" ")[0].replace(".", "")
            tanhuma.set_funcs(parse, grab_title_lambda, reorder_test_lambda, reorder_modify)
            tanhuma.run()
    else:
        en_parshiot.insert(0, "Foreword")
        en_parshiot.insert(1, "Introduction")
        he_parshiot.insert(0, u"פתח דבר")
        he_parshiot.insert(1, u"הקדמה")
        file_name = "Midrash-Tanhuma-Yelammedenu.xml"
        title = "Complex Midrash Tanchuma"
        tanhuma = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, en_parshiot)
        grab_title_lambda = lambda x: x[0].tag == "title"
        p = re.compile("\d+\.")
        reorder_test_lambda = lambda x: x.tag != "ftnote" and p.match(x.text) is not None
        def reorder_modify(text):
            return text.split(" ")[0].replace(".", "")
        tanhuma.set_funcs(parse, grab_title_lambda, reorder_test_lambda, reorder_modify)
        tanhuma.run()