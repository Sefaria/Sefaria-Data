import django
django.setup()
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
from sources.functions import *
import bleach
from lxml import etree

def preparser(root):
    books = ["Joshua", "Judges", "I Samuel", "II Samuel", "I Kings", "II Kings"]
    book = -1
    curr_book = None
    new_root = []
    ch_count = 0
    for i, x in enumerate(root):
        if len(x) == 1 and x.tag != "p":
            for grandchild in x[0]:
                x.append(grandchild)
            chapter_txt = re.search("Chapters? \S+\.", x[0].text).group(0)
            x.text = chapter_txt
            if x.text == "Chapter 1.":
                if curr_book is not None:
                    new_root.append(curr_book)
                book += 1
                curr_book = etree.SubElement(root, "book")
                curr_book.text = books[book]
            curr_book.append(x)
    new_root.append(curr_book)
    root.clear()
    for curr_book in new_root:
        root.append(curr_book)
    return root

def reorder_modify(text):
    return bleach.clean(text, strip=True)

def tester(x):
    #Chapter 1.
    return x.tag == "p" and re.search("Chapters? \d+.{,30}\.", x.text)

if __name__ == "__main__":
    #add_term("Preface", u"פתח דבר", "pseudo_toc_categories", "http://localhost:8000")
    #create_schema("Responsa to Chaplains", u"משהו", ["Halakhah"])
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SEFARIA_SERVER
    allowed_tags = ["book", "intro", "bibl", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix", "h1"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "The Early Prophets"
    post_info["versionSource"] = "http://www.sefaria.org"
    title = "The Early Prophets"
    file_name = "The_Early_Prophets.xml"
    lines = open(file_name, 'r', encoding='cp1252').read()
    parser = XML_to_JaggedArray(title, lines, allowed_tags, allowed_attributes, versionInfo=post_info, change_name=True,
                                titled=True, print_bool=True)
    parser.set_funcs(reorder_modify=reorder_modify, reorder_test=tester, preparser=preparser)
    parser.run()