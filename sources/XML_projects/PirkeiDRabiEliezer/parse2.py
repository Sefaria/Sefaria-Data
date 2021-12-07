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
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "intro", "part", "chapter", "p", "h1", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Pirke de Rabbi Eliezer, trans. Gerald Friedlander, London, 1916"
    post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001020236"
    title = "Pirkei DeRabbi Eliezer"
    file_name = "PirkeiDRabiEliezer.xml"

    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                titled=True, deleteTitles=False)
    parser.set_funcs(reorder_test=lambda x: False, reorder_modify=reorder_modify)
    parser.run()

