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


def get_dict_of_names(file):
    import csv
    reader = csv.reader(open(file))
    dict = {}
    for row in reader:
        dict[row[0]] = row[1]
    return dict




def change_priority(dict_of_names):
    pass

def modify_before_post(text_arr):
    prev_pasuk = None
    text_dict = {}
    for perek, comments in enumerate(text_arr):
        text_dict[perek+1] = {}
        for pasuk, comm in enumerate(comments):
            matches = re.findall("(\[\[(\d+)\]\])", comm)
            assert len(matches) in [0, 1]
            if matches:
                pasuk = int(matches[0][1])
                comm = comm.replace(matches[0][0], "")
            else:
                assert prev_pasuk
                pasuk = prev_pasuk

            if pasuk not in text_dict[perek+1]:
                text_dict[perek+1][pasuk] = []
            text_dict[perek+1][pasuk].append(comm)
            prev_pasuk = pasuk
        text_dict[perek+1] = convertDictToArray(text_dict[perek+1])
    return convertDictToArray(text_dict)


if __name__ == "__main__":
    #add_term("Preface", u"פתח דבר", "pseudo_toc_categories", "http://localhost:8000")
    #create_schema("Responsa to Chaplains", u"משהו", ["Halakhah"])
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix", "h1"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "The Metsudah Tanach series, Lakewood, N.J"
    post_info["versionSource"] = "https://www.judaicaplace.com/search/brand/Metsudah-Publications/"
    Judges = {"base": "Judges", "comm": "Rashi on Judges", "base_file": "Judges/Metsudah-Shoftim.xml", "comm_file": "Judges/Rashi.xml"}
    Shmuel_I = {"base": "Shmuel I", "comm": "Rashi on Shmuel I", "base_file": "Shmuel I/Metsudah-Shmuel-I.xml", "comm_file": "Shmuel I/Rashi.xml"}
    Shmuel_II = {"base": "Shmuel II", "comm": "Rashi on Shmuel II", "base_file": "Shmuel II/Metsudah-Shmuel-II.xml", "comm_file": "Shmuel II/Rashi.xml"}

    for book in [Shmuel_II, Judges, Shmuel_I]:
        title = book["base"]
        num_chapters = len(library.get_index(title).all_section_refs())
        file_name = book["base_file"]
        chapter_names = [el for el in range(1, num_chapters+1)]

        parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, array_of_names=chapter_names, change_name=True, image_dir="./images",                                titled=True)
        parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify)
        parser.run()

        title = book["comm"]
        file_name = book["comm_file"]

        parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, array_of_names=chapter_names, change_name=True, image_dir="./images",
                                    titled=True)
        parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify, modify_before_post=modify_before_post)
        parser.run()








