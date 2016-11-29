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
        xref_start = re.findall("<xref.*?>", text_arr[index])
        xref_end = re.findall("</xref.*?>", text_arr[index])
        xrefs = xref_start + xref_end
        for xref in xrefs:
            text_arr[index] = text_arr[index].replace(xref, "")

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

    arr = ["I", "II", "III", "IV", "V", "VI", "VII"]
    for i in range(7):
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
        if i < 6:
            default = JaggedArrayNode()
            default.depth = 2
            default.default = True
            default.sectionNames = ["Chapter", "Paragraph"] if i < 6 else ["Letter", "Paragraph"]
            default.addressTypes = ["Integer", "Integer"]
            default.key = "default"
            pt.append(subject)
            pt.append(default)
            book.append(pt)
        else:
            pt.append(subject)
            glossary_eng = ["Alef", "Bet", "Gimel", "Daled", "Heh", "Vav", "Zayin", "Chet", "Tet", "Yod", "Kaf", "Lamed", "Mem", "Nun", "Samekh",
                    "Ayin", "Peh", "Tzadi", "Kof", "Resh", "Shin", "Tav"]
            for j in range(len(glossary_eng)):
                gloss_node = JaggedArrayNode()
                gloss_node.depth = 1
                gloss_node.sectionNames = ["Paragraph"]
                gloss_node.addressTypes = ["Integer"]
                gloss_node.key = "Letter {}".format(glossary_eng[j])
                gloss_node.add_title("Letter {}".format(glossary_eng[j]), "en", primary=True)
                gloss_node.add_title(u"אות {}".format(numToHeb(j+1)), "he", primary=True)
                pt.append(gloss_node)
            book.append(pt)



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
    post_info["versionTitle"] = "Moses Cordovero’s Introduction to Kabbalah, Annotated trans. of Or ne'erav, Ira Robinson, 1994."
    post_info["versionSource"] = "http://www.ktav.com/index.php/moses-cordovero-s-introduction-to-kabbalah.html"
    post_info["language"] = "en"
    allowed_tags = ["book", "intro", "part", "appendix", "chapter", "p", "ftnote", "title"]
    structural_tags = ["title"] #this is not all tags with structural significance, but just
                                #the ones we must explicitly mention, because it has no children,
                                #we want what comes after it until the next instance of it to be its children anyway
    allowed_attributes = ["id"]
    file_name = "english_or_neerav.xml"
    title = "Or Neerav"
    ramak = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, parse)


    create_schema()
    ramak.run()
