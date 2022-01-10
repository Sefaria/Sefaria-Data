# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach
import os
def reorder_modify(text):
    return bleach.clean(text, strip=True)

def reorder_test(child):
    return child.tag == "chapter" and str(child.text).isdigit()


post_info = {}
post_info["language"] = "en"
post_info["server"] = "http://ste.sandbox.sefaria.org"
allowed_tags = ["book", "intro", "bibl", "part", "h1", "h2", "h3", "p", "chapter", "ftnote", "part", "img", "title", "ol", "footnotes", "appendix"]
allowed_attributes = ["id", "src"]
p = re.compile("\d+a?\.")

files = [f for f in os.listdir(".") if f.endswith(".xml")]
for f in files:
    if "Major_themes" in f or "Studies_in_Torah" in f:
        print(f)
        title = f[0:-3].split("Berkovitz-")[-1].replace("_", " ").title()
        post_info["versionTitle"] = "Commentary on the Torah by Ramban (Nachmanides). Translated and annotated by Charles B. Chavel. New York, Shilo Pub. House, 1971-1976"
        post_info["versionSource"] = "https://www.nli.org.il/he/books/NNL_ALEPH002108945/NLI"
        versionInfo = [["Index Title", title],
                       ["Version Title",
                        "Commentary on the Torah by Ramban (Nachmanides). Translated and annotated by Charles B. Chavel. New York, Shilo Pub. House, 1971-1976"],
                       ["Language", "he"],
                       ["Version Source", "https://www.nli.org.il/he/books/NNL_ALEPH002108945/NLI"],
                       ["Version Notes", ""]]
        with open(f) as file:
            lines = file.read()
            parser = XML_to_JaggedArray(title, lines, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                        titled=True, print_bool=True, remove_chapter=False, versionInfo=versionInfo)
            parser.set_funcs(reorder_test=reorder_test, reorder_modify=reorder_modify)
            parser.run()