# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from parsing_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach

SERVER = "http://proto.sefaria.org"

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
    #add_term("Preface", u"פתח דבר", "pseudo_toc_categories", "http://localhost:8000")
    #create_schema("Responsa to Chaplains", u"משהו", ["Halakhah"])
    post_info = {}
    volume = 2
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["volume", "book", "intro", "preface", "bibl", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Trans. Salomon Munk, Paris, 1856 [fr]"
    post_info["versionSource"] = "http://beta.nli.org.il/he/books/NNL_ALEPH001236429/NLI"
    title = "Moreh Nevukhim"
    file_name = "full_text.xml"
    #
    #
    # array_of_names = [u"INTRODUCTION", u"PREMIÈRE PARTIE"]
    # array_of_names += [unicode(x) for x in range(1, 77)]
    # array_of_names += [u"ADDITIONS ET RECTIFICATIONS"]
    # chapters = range(1, 25)
    # counter = 0
    # for i, name in enumerate(array_of_names):
    #     if name == "chapter":
    #         array_of_names[i] = str(chapters[counter])
    #         counter += 1

    with open(file_name) as f:
        file = f.read()
    parser = XML_to_JaggedArray(title, file, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                titled=True, print_bool=True)
    parser.set_funcs(reorder_modify=reorder_modify)
    parser.run()
