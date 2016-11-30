# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
from XML_to_JaggedArray import XML_to_JaggedArray
import sys
sys.path.append('../')
from functions import *
sys.path.append('../../../')
from sefaria.model import *

'''Every node whose first element is a title is the node's title.  Then remove these titles possibly.
  Every other title has structural significance if it has a bold tag as a child
    Titles can structure text
    Footnotes
    Also consider how to decipher JA_array or allowed_tags automatically
    '''
def parse(text_arr):
    assert type(text_arr) is list
    for index, text in enumerate(text_arr):
        text_arr[index] = text_arr[index].replace("<bold>", "<b>").replace("<italic>", "<i>").replace("</bold>", "</b>").replace("</italic>", "</i>")
    return text_arr


def create_schema():
    book = SchemaNode()
    book.key = "ramak"
    book.add_title(u"אור נערב", "he", primary=True)
    book.add_title("Or Neerav", "en", primary=True)

    intro = JaggedArrayNode()
    intro.add_title("Introduction", "en", primary=True)
    intro.add_title(u"הקדמה", "he", primary=True)
    intro.depth = 1
    intro.sectionNames = ["Paragraph"]
    intro.addressTypes = ["Integer"]
    intro.key = "intro"
    book.append(intro)

    arr = ["I", "II", "III", "IV", "V", "VI"]
    for i in range(6):
        pt = SchemaNode()
        pt.key = "pt"+str(i)+"schema"
        pt.add_title("PART " + arr[i], "en", primary=True)
        pt.add_title(u"חלק "+numToHeb(1+i), "he", primary=True)

        subject = JaggedArrayNode()
        subject.add_title("Subject", "en", primary=True)
        subject.add_title(u"נושא", "he", primary=True)
        subject.key = "subject"
        subject.depth = 1
        subject.sectionNames = ["Paragraph"]
        subject.addressTypes = ["Integer"]

        default = JaggedArrayNode()
        default.depth = 2
        default.default = True
        default.sectionNames = ["Chapter", "Paragraph"]
        default.addressTypes = ["Integer", "Integer"]
        default.key = "default"
        pt.append(subject)
        pt.append(default)
        book.append(pt)

    pt7 = JaggedArrayNode()
    pt7.add_title("PART VII", "en", primary=True)
    pt7.add_title(u"חלק ז", "he", primary=True)
    pt7.depth = 1
    pt7.sectionNames = ["Paragraph"]
    pt7.addressTypes = ["Integer"]
    pt7.key = "pt7"
    book.append(pt7)

    appendix = SchemaNode()
    appendix.add_title("Appendix The Introductory Material", "en", primary=True)
    appendix.add_title(u"נספח: הקדמות", "he", primary=True)
    appendix.key = "appendix"

    subject = JaggedArrayNode()
    subject.add_title("Subject", "en", primary=True)
    subject.add_title(u"נושא", "he", primary=True)
    subject.key = "subject"
    subject.depth = 1
    subject.sectionNames = ["Paragraph"]
    subject.addressTypes = ["Integer"]

    default = JaggedArrayNode()
    default.depth = 2
    default.default = True
    default.sectionNames = ["Chapter", "Paragraph"]
    default.addressTypes = ["Integer", "Integer"]
    default.key = "default"
    appendix.append(subject)
    appendix.append(default)

    footnotes_array = ["Introduction", "PART I", "PART II", "PART III", "PART IV", "PART V", "PART VI", "PART VII", "Appendix The Introductory Material"]
    footnotes_heb = [u"הקדמה", u"חלק א", u"חלק ב", u"חלק ג", u"חלק ד", u"חלק ה", u"חלק ו", u"חלק ז", u"נספח"]
    footnotes = SchemaNode()
    footnotes.key = "footnotes"
    footnotes.add_title("Footnotes", "en", primary=True)
    footnotes.add_title(u"הערות", "he", primary=True)
    for i in range(len(footnotes_array)):
        node = JaggedArrayNode()
        if footnotes_array[i] == "Introduction" or footnotes_array[i] == "PART VII":
            node.depth = 1
            node.sectionNames = ["Paragraph"]
            node.addressTypes = ["Integer"]
        else:
            node.depth = 2
            node.sectionNames = ["Chapter", "Paragraph"]
            node.addressTypes = ["Integer", "Integer"]
        node.key = footnotes_array[i]
        node.add_title(footnotes_array[i], "en", primary=True)
        node.add_title(footnotes_heb[i], "he", primary=True)
        footnotes.append(node)


    book.append(appendix)
    book.append(footnotes)

    book.validate()
    index = {
    "title": title,
    "categories": ["Kabbalah"],
    "schema": book.serialize()
    }
    post_index(index)

if __name__ == "__main__":
    post_info = {}
    post_info["versionTitle"] = "hi"
    post_info["versionSource"] = "hi"
    post_info["language"] = "en"
    allowed_tags = ["book", "intro", "part", "appendix", "chapter", "p", "ftnote", "title"]
    structural_tags = ["title"] #this is not all tags with structural significance, but just
                                #the ones we must explicitly mention, because it has no children,
                                #we want what comes after it until the next instance of it to be its children anyway
    allowed_attributes = ["id"]
    file_name = "../sources/DC labs/Robinson_MosesCordoveroIntroductionToKabbalah.xml"
    title = "Or Neerav"
    ramak = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, parse)


    create_schema()
    ramak.run()
