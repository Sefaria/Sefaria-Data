# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach

SERVER = "http://draft.sefaria.org"

def reorder_modify(text):
    return bleach.clean(text, strip=True)



if __name__ == "__main__":
    vs = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002610264"
    choshen_vt = "Code of Hebrew Law by Chaim N. Denburg, Hoshen Hamishpat 1-27"
    yoreh_vt = "Code of Hebrew Law by Chaim N. Denburg, Yoreh De'ah 335-403"
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = choshen_vt
    post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002610264"
    title = "Choshen Mishpat"
    file_name = "choshen mishpat.xml"

    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                titled=True)
    parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify)
    #parser.run()

    post_info["versionTitle"] = yoreh_vt
    post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002610264"
    title = "Yoreh Deah"
    file_name = "yoreh deah.xml"

    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                titled=True)
    parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify)
    parser.run()
