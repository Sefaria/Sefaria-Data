# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach

SERVER = "http://draft.sefaria.org"

def create_schema(en_title, he_title, categories, parser):
    root = SchemaNode()
    root.add_primary_titles(en_title, he_title)

    node = JaggedArrayNode()
    node.add_structure(["Paragraph"])
    node.add_shared_term("Introduction")
    node.key = "intro"
    root.append(node)

    with open("en_to_he.csv") as file:
        reader = UnicodeReader(file)
        for row in reader:
            assert len(row) is 2
            en, he = row[0], row[1]
            if en == "English Chapter Names":
                continue
            en = parser.cleanNodeName(en)
            new_node = JaggedArrayNode()
            new_node.add_primary_titles(en, he)
            new_node.add_structure(["Paragraph"])
            root.append(new_node)

    root.validate()
    index = {
        "schema": root.serialize(),
        "title": en_title,
        "categories": categories,
    }
    post_index(index, server=SERVER)


def reorder_modify(text):
    return bleach.clean(text, strip=True)

if __name__ == "__main__":
    #add_term("Preface", u"פתח דבר", "pseudo_toc_categories", "http://localhost:8000")

    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Responsa in Wartime"
    post_info["versionSource"] = "http://primo.nli.org.il/"
    title = "Responsa in Wartime"
    file_name = "ResponsaInWartime.xml"

    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                titled=True)
    create_schema("Responsa in Wartime", u'שו"ת בעת מלחמה', ["Halakhah"], parser)
    parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify)
    parser.run()



books = [library.get_index(book) for book in library.get_indexes_in_category("Mishneh Torah")]
books = [book.title for book in books for v in book.versionSet() if "Philip Birnbaum" in v.versionTitle]
versionTitle = "Maimonides' Mishneh Torah, edited by Philip Birnbaum, New York, 1967"
for book in books:
    print "./run scripts/move_draft_text.py '{}' -v 'en:{}' -d 'https://www.sefaria.org' -k 'kAEw7OKw5IjZIG4lFbrYxpSdu78Jsza67HgR0gRBOdg'".format(book, versionTitle)
