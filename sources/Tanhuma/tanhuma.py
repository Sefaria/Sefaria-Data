# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
from XML_to_JaggedArray import XML_to_JaggedArray
import sys
sys.path.append('../')
from functions import *
sys.path.append('../../../')
from sefaria.model import *

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
    en_parshiot.append("Foreword")
    en_parshiot.append("Introduction")
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
    post_info = {}
    post_info["versionTitle"] = "Midrash Tanhuma-Yelammedenu, trans. Samuel A. Berman"
    post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001350458"
    post_info["language"] = "en"
    allowed_tags = ["book", "intro", "foreword", "part", "chapter", "p", "ftnote", "title"]
    allowed_attributes = ["id"]
    file_name = "Midrash-Tanhuma-Yelammedenu.xml"
    title = "Complex Midrash Tanchuma"
    tanhuma = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, en_parshiot)
    grab_title_lambda = lambda x: x[0].tag == "title"
    reorder_lambda = lambda x: False
    tanhuma.set_funcs(parse, grab_title_lambda, reorder_lambda)


    tanhuma.run()