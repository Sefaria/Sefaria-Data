# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from parsing_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach

SERVER = "http://ste.sefaria.org"

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
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "intro", "bibl", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix", "h1"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Responsa on Contemporary Jewish Women's Issues"
    post_info["versionSource"] = "http://www.sefaria.org"
    title = "Responsa on Contemporary Jewish Women's Issues"
    file_name = "Responsa_on_Contemporary_Jewish_Womens_Issues.xml"

    array_of_names = ['intro', 'part', 'chapter', 'part', 'chapter', 'chapter', 'chapter', 'chapter', 'chapter', 'chapter', 'chapter', 'chapter', 'chapter', 'chapter', 'part', 'chapter', 'chapter', 'chapter', 'chapter', 'part', 'chapter', 'chapter', 'chapter', 'chapter', 'chapter', 'part', 'chapter', 'chapter', 'chapter', 'chapter', 'appendix', 'bibl']
    chapters = range(1, 25)
    counter = 0
    for i, name in enumerate(array_of_names):
        if name == "chapter":
            array_of_names[i] = str(chapters[counter])
            counter += 1

    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                titled=True, print_bool=True, remove_chapter=False, array_of_names=array_of_names)
    parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify)
    parser.run()

