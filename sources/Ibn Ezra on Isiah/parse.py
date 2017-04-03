# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *


if __name__ == "__main__":
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = sys.argv[1]
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Commentary of Ibn Ezra on Isaiah; trans. by M. Friedlander, 1873"
    post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001338443"
    file_name = "IbnEzra_Isiah.xml"
    title = "Ibn Ezra on Isaiah"


    mapping = {}
    array_of_names = ["Prelude"]
    for i in range(66):
        array_of_names.append(i+1)
    array_of_names += ["Addenda", "Translators Foreword"]
    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, array_of_names)
    parser.set_funcs()
    parser.run()