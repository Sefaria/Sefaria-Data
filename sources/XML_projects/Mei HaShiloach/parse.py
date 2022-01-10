# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach

SERVER = "https://ste.cauldron.sefaria.org"

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


def tester(x):
    return x.tag == "h1"

if __name__ == "__main__":
    #add_term("Preface", u"פתח דבר", "pseudo_toc_categories", "http://localhost:8000")
    #create_schema("Responsa to Chaplains", u"משהו", ["Halakhah"])
    post_info = {}
    volume = 2
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["volume", "book", "ack", "intro", "preface", "bibl", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Rereading The Rabbis: A Woman's Voice. By Judith Hauptman"
    post_info["versionSource"] = "https://www.amazon.com/Rereading-Rabbis-Womans-Radical-Traditions/dp/0813334063"
    title = "Mei HaShiloach"
    file_name = "LivingWaters.xml"

    with open(file_name) as f:
        file = f.read()
    parser = XML_to_JaggedArray(title, file, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                titled=True, print_bool=True)
    parser.set_funcs(reorder_modify=reorder_modify, reorder_test=tester)
    parser.run()
