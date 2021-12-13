import django
django.setup()
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
from sources.functions import *
from lxml import etree
import bleach

def preparser(root):
    chs = [x for x in root if x.tag != "p"]
    curr_book = etree.SubElement(root, "book")
    curr_book.text = "Introduction"
    curr_books = []
    ch_count = 0
    for ch in chs:
        if ch.text.upper() in ["GENESIS", "EXODUS", "LEVITICUS", "NUMBERS", "DEUTERONOMY"]:
            curr_books.append(curr_book)
            curr_book = etree.SubElement(root, "book")
            curr_book.text = ch.text.upper()
            ch_count = 0
        else:
            if ch.text == "\n" and ch.tag == "chapter":
                ch_count += 1
                ch.text = str(ch_count)
            curr_book.append(ch)
    curr_books.append(curr_book)
    root.clear()
    for c in curr_books:
        print(c.text)
        for y in c:
            print(" -> " + y.text)
        root.append(c)
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
    allowed_tags = ["book", "intro", "bibl", "part", "chapter", "p", "ftnote", "title", "preface", "ol", "footnotes", "appendix", "h1"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Torah"
    post_info["versionSource"] = "http://www.sefaria.org"
    title = "Torah"
    file_name = "The_Five_Books_of_Moses.xml"
    lines = open(file_name, 'r', encoding="cp1252").read()
    parser = XML_to_JaggedArray(title, lines, allowed_tags, allowed_attributes, versionInfo=post_info, change_name=True,
                                titled=True, print_bool=True)
    parser.set_funcs(reorder_modify=reorder_modify, reorder_test=lambda x: False, preparser=preparser)
    parser.run()