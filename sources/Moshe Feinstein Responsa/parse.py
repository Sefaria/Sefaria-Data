# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach

def reorder_modify(text):
    return bleach.clean(text, strip=True)

if __name__ == "__main__":
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = sys.argv[1]
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Responsa of Rav Moshe Feinstein, trans. by Moshe David Tendler; Vol. 1: Care of the Critically Ill, Hoboken, NJ: Ktav, 1996."
    post_info["versionSource"] = "http://www.ktav.com/index.php/responsa-of-rav-moshe-feinstein.html"
    title = "Responsa of R Moshe Feinstein Vol 1"
    file_name = "responsa.xml"


    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images")
    parser.set_funcs(reorder_test=lambda x: x.tag == "title" and x.text.find("<bold>") == 0, reorder_modify=reorder_modify)
    parser.run()