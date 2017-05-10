# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import sys
import re
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from lxml import etree
import BeautifulSoup

def create_schema(en_he_parshiot):
    book = SchemaNode()
    book.add_title("Midrash Tanchuma Buber", "en", primary=True)
    book.add_title(u"תנחומא - בובר", "he", primary=True)
    book.key = "buber_midrash_tanhuma"

    appendices = ["Sh'lach", "Korach", "Chukat", "Devarim", "Vaetchanan", "Re'eh"]
    en_parshiot = []

    for index, parsha_tuple in enumerate(en_he_parshiot):
        en_name = parsha_tuple[0]
        print en_name
        if en_name == "Vayeilech":
            continue
        appendix = None
        parsha = JaggedArrayNode()
        parsha.key = en_name
        parsha.add_title(en_name, "en", primary=True)
        parsha.add_title(parsha_tuple[1], "he", primary=True)
        parsha.sectionNames = ["Siman", "Paragraph"]
        parsha.depth = 2
        parsha.addressTypes = ["Integer", "Integer"]
        if en_name in appendices:
            appendix = JaggedArrayNode()
            he_title = u"הוספה ל{}".format(parsha_tuple[1])
            appendix.add_primary_titles("Appendix to {}".format(en_name), he_title)
            appendix.add_structure(["Siman", "Paragraph"])
        en_parshiot.append(en_name)
        book.append(parsha)
        if appendix is not None:
            en_parshiot.append("Appendix to {}".format(en_name))
            book.append(appendix)

    footnotes = SchemaNode()
    footnotes.key = "footnotes"
    footnotes.add_title("Footnotes", "en", primary=True)
    footnotes.add_title(u"הערות", "he", primary=True)

    for index, parsha_tuple in enumerate(en_he_parshiot):
        en_name = parsha_tuple[0]
        print en_name
        if en_name == "Vayeilech":
            continue
        appendix = None
        parsha = JaggedArrayNode()
        parsha.key = "footnotes"+en_name
        parsha.add_title(en_name, "en", primary=True)
        parsha.add_title(parsha_tuple[1], "he", primary=True)
        parsha.sectionNames = ["Paragraph"]
        parsha.depth = 1
        parsha.addressTypes = ["Integer"]
        if en_name in appendices:
            appendix = JaggedArrayNode()
            he_title = u"הוספה ל{}".format(parsha_tuple[1])
            appendix.add_primary_titles("Appendix to {}".format(en_name), he_title)
            appendix.add_structure(["Paragraph"])
        if appendix is not None:
            footnotes.append(appendix)
        footnotes.append(parsha)

    book.append(footnotes)


    book.validate()
    index = {
        "title": "Midrash Tanchuma Buber",
        "schema": book.serialize(),
        "categories": ["Midrash"]
    }
    #post_index(index, server="http://ste.sefaria.org")
    return en_parshiot


def extractIDsAndSupNums(text):
    ft_ids = []
    ft_sup_nums = []
    xrefs = BeautifulSoup.BeautifulSoup(text).findAll('xref')
    for xref in xrefs:
        ft_ids.append(xref['rid'])
        ft_sup_nums.append(xref.text)

    return ft_ids, ft_sup_nums


def getPositions(text):
    pos = []
    all = re.findall('<sup><xref.*?>\d+</xref></sup>', text)
    for each in all:
        pos.append(text.find(each))
    return pos


'''
first extract ids and numbers
create dictionary where each id corresponds to text of footnote
find position where footnote goes, if tags are there, create critera for deleting them
delete them
put in <sup>num</sup><i class="footnote">
'''

def buildFtnoteText(num, text):
    return u'<sup>{}</sup><i class="footnote">{}</i>'.format(num, text)

def parse(text_arr, footnotes):
    key_of_xref = 'rid'

    assert type(text_arr) is list
    ftnote_texts = []
    for index, text in enumerate(text_arr):
        text_arr[index] = text_arr[index].replace("<bold>", "<b>").replace("<italic>", "<i>").replace("</bold>", "</b>").replace("</italic>", "</i>")
        text_arr[index] = text_arr[index].replace("<li>", "<br>").replace("</li>", "")
        text_arr[index] = text_arr[index].replace("3465", "&lt;").replace("3467", "&gt;")

        ft_ids, ft_sup_nums = extractIDsAndSupNums(text_arr[index])

        ft_pos = getPositions(text_arr[index])

        assert len(ft_ids) == len(ft_sup_nums) == len(ft_pos)

        for i in range(len(ft_ids)):
            reverse_i = len(ft_ids) - i - 1
            ftnote_text = footnotes[ft_ids[reverse_i]]
            text_to_insert = buildFtnoteText(ft_sup_nums[reverse_i], ftnote_text)
            pos = ft_pos[reverse_i]
            text_arr[index] = u"{}{}{}".format(text_arr[index][0:pos], text_to_insert, text_arr[index][pos:])

        all = re.findall('<sup><xref.*?>\d+</xref></sup>', text_arr[index])
        for each in all:
            text_arr[index] = text_arr[index].replace(each, "")


    return text_arr



def modifyBeforeBleach(text):
    return text.replace("&#x003C;", "3465").replace("&#x003E;", "3467")

if __name__ == "__main__":
    import csv
    print 'got here'
    en_he_parshiot = [("Introduction", u"הקדמה")]
    with open("../../../Sefaria-Project/data/tmp/parsha.csv") as parsha_file:
        parshiot = csv.reader(parsha_file)
        parshiot.next()
        order = 1
        for row in parshiot:
            (en, he, ref) = row
            if en == "Lech-Lecha":
                en = "Lech Lecha"
            he = he.decode('utf-8')
            en_he_parshiot.append((en, he))


    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = sys.argv[2]
    allowed_tags = ["book", "volume", "intro", "foreword", "part", "chapter", "p", "ftnote", "title", "ol", "ul", "table"]
    allowed_attributes = ["id"]
    grab_title_lambda = lambda x: x[0].tag == "title"
    p = re.compile("\d+a?\.")
    reorder_test_lambda = lambda x: x.tag == "title" and p.match(x.text) is not None
    def reorder_modify(text):
        text = text.split(" ")
        marker = text[0]
        text = " ".join(text[1:])
        if marker.split(".")[-1] == "":
            return marker.split(".")[0]
        else:
            return marker.split(".")[-1]

    if sys.argv[1] == "Buber":
        title = "Midrash Tanchuma Buber"
        en_parshiot = create_schema(en_he_parshiot)
        file_name = "buber.xml"
        post_info["versionTitle"] = "Midrash Tanhuma, S. Buber Recension; trans. by John T. Townsend, 1989."
        post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001095601"
    else:
        post_info["versionTitle"] = "Midrash Tanhuma-Yelammedenu, trans. Samuel A. Berman"
        post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001350458"
        en_he_parshiot.insert(0, ("Foreword", u"פתח דבר"))
        file_name = "Midrash-Tanhuma-Yelammedenu.xml"
        title = "Midrash Tanchuma"
        en_parshiot = [list(x) for x in zip(*en_he_parshiot)][0]

    tanhuma = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, en_parshiot)
    tanhuma.set_funcs(grab_title_lambda, reorder_test_lambda, reorder_modify, modifyBeforeBleach)
    tanhuma.run()