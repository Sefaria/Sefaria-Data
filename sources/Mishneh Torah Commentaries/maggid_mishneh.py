# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from bs4 import *
from BeautifulSoup import Tag, NavigableString
import bleach
from sources.functions import post_text
import re
from sources.functions import *

SERVER="http://proto.sefaria.org"
class Mishneh_Torah_Commentary:
    def __init__(self, file, segment_marker=None, comment_marker=None):
        self.file = file
        self.soup = BeautifulSoup(open(file))
        self.segment_marker = segment_marker
        self.comment_marker = comment_marker
        self.text = {}
        self.he_name = ""
        pass

    def set_fields(self, he_name, segment_marker, comment_marker, text={}):
        self.text = text
        self.he_name = he_name
        self.segment_marker = segment_marker
        self.comment_marker = comment_marker


    def get_book_and_perek(self, segment_for_comment, new_segment, prev_perek):
        perek_header = segment_for_comment.find_previous("span", attrs={"style": self.segment_marker})
        while perek_header.text.find(" - ") == -1:
            perek_header = perek_header.find_previous("span", attrs={"style": self.segment_marker})
        book, perek = perek_header.text.split(u" - ")
        if perek.startswith(u"פרק"):
            perek_num_word = " ".join(perek.split(" ")[1:])
            perek = perek_to_number(perek_num_word)
            return book, perek
        else:
            self.text[book][prev_perek][new_segment] = [perek]
            return book, prev_perek


    def parse_comment(self, comment):
        '''
        1. If it's text add text
        2. If it's bold add node.text
        3. If it's
        '''
        comm_text = ""
        text_list = []
        counter = 0
        for count, node in enumerate(comment):
            if node.name == "br":
                comm_text += "<br>"
            elif node.name == "b":
                if node.text.endswith("."):
                    if len(comm_text) > 0:
                        text_list.append(comm_text)
                        comm_text = ""
                comm_text += "<b>"+node.text+"</b>"
            elif node.name == None:
                comm_text += node
            else:
                comm_text += node.text
        if len(comm_text) > 0:
            text_list.append(comm_text)
        return text_list


    def parse(self):
        prev_segment = None
        prev_perek = None
        all_comments = self.soup.findAll(attrs={"style": self.comment_marker})
        for i, comment in enumerate(all_comments):
            assert self.he_name in comment.parent.text[0:10] or self.he_name.split(" ")[1] in comment.parent.text[0:10]
            segment_for_comment = comment.find_previous("span", attrs={"style": self.segment_marker})
            new_segment = getGematria(segment_for_comment.text)
            book, perek = self.get_book_and_perek(segment_for_comment, new_segment, prev_perek)

            if book not in self.text:
                self.text[book] = {}

            if perek not in self.text[book]:
                self.text[book][perek] = {}

            if new_segment not in self.text[book][perek]:
                self.text[book][perek][new_segment] = self.parse_comment(comment)
            else:
                self.text[book][perek][new_segment] += [self.parse_comment(comment)]

            prev_segment = new_segment
            prev_perek = perek

        for book_name, book_text in self.text.items():
            for perek in book_text.keys():
                self.text[book_name][perek] = convertDictToArray(self.text[book_name][perek])
            self.text[book_name] = convertDictToArray(self.text[book_name])


def create_schema(en_title, he_title, c):
    assert u"משנה תורה" in he_title
    assert "Mishneh Torah" in en_title
    index = library.get_index(en_title)
    base_text_title, category = en_title, index.categories[-1]
    he_title = u"{} על {}".format(c["he_name"], he_title)
    en_title = "{} on {}".format(c["name"], en_title)
    root = JaggedArrayNode()
    root.add_primary_titles(en_title, he_title)
    root.add_structure(["Chapter", "Halacha", "Comment"])
    root.validate()
    index = {
        "schema": root.serialize(),
        "dependence": "Commentary",
        "base_text_titles": [base_text_title],
        "base_text_mapping": "many_to_one",
        "title": en_title,
        "categories": ["Halakha", "Commentary", "Mishneh Torah", category]
    }
    post_index(index, server=SERVER)
    return en_title


def post_commentator(commentator, books, hebrew_to_english):
    for book_name, book_text in books.items():
        he_book_name = u"{}, {}".format(u"משנה תורה", book_name)
        if he_book_name not in hebrew_to_english:
            print he_book_name
            continue
        else:
            en_book_name = hebrew_to_english[he_book_name]
        book_name = create_schema(en_book_name, he_book_name, commentator)
        print book_name
        book_text = {
            "text": book_text,
            "language": "he",
            "versionTitle": "ToratEmet",
            "versionSource": "http://www.toratemetfreeware.com/online/d_root__035_mshnh_torh_lhrmbm.html"
        }
        post_text(book_name, book_text, server=SERVER)


if __name__ == "__main__":
    rambam_books = map(lambda x: library.get_index(x), library.get_indexes_in_category("Mishneh Torah"))
    hebrew_to_english = {rambam_book.get_title("he"): rambam_book.get_title("en") for rambam_book in rambam_books}
    files = filter(lambda x: x.endswith(".html") and not x.startswith("errors"), os.listdir("."))
    maggid = {"name": "Maggid Mishneh", "segment_marker": 'color:RGB(45,104,176);', "comment_marker": 'color:RGB(122,13,134);', "he_name": u"מגיד משנה", "exclude": "madah.html"}
    lehem = {"name": "Lehem Mishneh", "segment_marker": 'color:RGB(45,104,176);', "comment_marker": "color:RGB(89,45,0);", "he_name": u"לחם משנה", "exclude": None}
    hasagot = {"name": "Hasagot HaRaavad", "comment_marker": 'color:RGB(15,74,172);', "segment_marker": 'color:RGB(45,104,176);', "he_name": u"""השגות הראב"ד""", "exclude": None}

    results = {}
    results["Maggid Mishneh"] = {}
    results["Lehem Mishneh"] = {}
    results["Hasagot HaRaavad"] = {}
    results["Peirush"] = {}

    #Parse peirush separately because it comments on only one book
    peirush = dict(maggid)
    peirush["exclude"] = None
    peirush["name"] = "Peirush"
    peirush["he_name"] = u"פירוש"
    MTC = Mishneh_Torah_Commentary("madah.html")
    MTC.set_fields(he_name=peirush["he_name"], segment_marker=peirush["segment_marker"], comment_marker=peirush["comment_marker"])
    MTC.parse()
    if MTC.text != {}:
        post_commentator(peirush, MTC.text, hebrew_to_english)
    results["Peirush"] = MTC.text

    dont_start = True
    #skip = ["nashim.html"]

    #parse the 3 remaining commentaries (not Peirush)
    for file in files:
        #if file in skip:
        #    continue
        if file != "nezikin.html" and dont_start:
            continue
        else:
            dont_start = False
        MTC = Mishneh_Torah_Commentary(file)

        for c in [maggid, lehem, hasagot]:
            if c["exclude"] == file:
                continue

            MTC.set_fields(he_name=c["he_name"], segment_marker=c["segment_marker"], comment_marker=c["comment_marker"], text={})
            MTC.parse()
            if MTC.text != {}:
                results[c["name"]].update(MTC.text)
                post_commentator(c, MTC.text, hebrew_to_english)
