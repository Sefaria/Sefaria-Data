# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from bs4 import *
from BeautifulSoup import Tag, NavigableString
import bleach
from sources.functions import post_text
import re
from sources.functions import *

SERVER="https://www.sefaria.org"
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


    def get_section_and_mishneh(self, segment_for_comment, new_segment, prev_mishneh):
        mishneh_header = segment_for_comment.find_previous("span", attrs={"style": self.segment_marker})
        while mishneh_header.text.find(" - ") == -1:
            mishneh_header = mishneh_header.find_previous("span", attrs={"style": self.segment_marker})
        section, mishneh = mishneh_header.text.split(u" - ")
        assert section.startswith(u"פרק")
        assert mishneh.startswith(u"משנה")
        section = getGematria(section.split(" ")[1])
        mishneh = getGematria(mishneh.split(" ")[1])
        return section, mishneh
        #else:
        #    self.text[section][prev_mishneh][new_segment] = [mishneh]
        #    return section, prev_mishneh


    def remove_i_tags(self, comment):
        found = re.findall("<b>\{.{1,2}\}</b>", comment)
        for find in found:
            comment = comment.replace(find, "")
        return comment


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
                        comm_text = self.remove_i_tags(comm_text)
                        if len(comm_text.replace(" ", "")) > 0:
                            text_list.append(comm_text)
                        comm_text = ""
                comm_text += "<b>"+node.text+"</b>"
            elif node.name == None:
                comm_text += node
            else:
                comm_text += node.text
        if len(comm_text) > 0:
            comm_text = self.remove_i_tags(comm_text)
            if len(comm_text.replace(" ", "")) > 0:
                text_list.append(comm_text)
        return text_list


    def parse(self):
        prev_segment = None
        prev_mishneh = None
        all_comments = self.soup.findAll(attrs={"style": self.comment_marker})
        for i, comment in enumerate(all_comments):
            assert self.he_name in comment.parent.text[0:25] or self.he_name.split(" ")[1] in comment.parent.text[0:25]
            section, mishneh = self.get_section_and_mishneh(comment, prev_segment, prev_mishneh)

            if section not in self.text:
                self.text[section] = {}

            if mishneh not in self.text[section]:
                self.text[section][mishneh] = {}

            self.text[section][mishneh] = self.parse_comment(comment)

            prev_mishneh = mishneh

        for section_name, section_text in self.text.items():
            self.text[section_name] = convertDictToArray(self.text[section_name])
        self.text = convertDictToArray(self.text)


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
        "collective_title": c["name"],
        "categories": ["Halakhah", "Mishneh Torah", "Commentary", c["name"], category]
    }
    print SERVER
    post_index(index, server=SERVER)
    return en_title


def get_alternate_spelling(section):
    import csv
    reader = csv.reader(open("spellings.csv"))
    for row in reader:
        if section == row[0].decode('utf-8'):
            return row[1].decode('utf-8')
    raise Exception


def post_commentator(commentator, sections, hebrew_to_english):
    for section_name, section_text in sections.items():
        he_section_name = u"{}, {}".format(u"משנה תורה", section_name)
        if he_section_name not in hebrew_to_english:
            he_section_name = get_alternate_spelling(he_section_name)
            assert he_section_name in hebrew_to_english
        en_section_name = hebrew_to_english[he_section_name]
        section_name = create_schema(en_section_name, he_section_name, commentator)
        print section_name
        section_text = {
            "text": section_text,
            "language": "he",
            "versionTitle": "ToratEmet",
            "versionSource": "http://www.toratemetfreeware.com/online/d_root__035_mshnh_torh_lhrmbm.html"
        }
        post_text(section_name, section_text, server=SERVER)



def terms(dict):
    add_term(dict["name"], dict["he_name"], scheme="commentary_works", server=SERVER)



def redo_kessef():
    kessef_titles = library.get_indices_by_collective_title("Kessef Mishneh")
    for section_title in kessef_titles:
        index = library.get_index(section_title)
        old_categories = index.categories
        assert len(old_categories) == 5 and old_categories[4].startswith("Sefer")
        new_categories = ["Halakhah", "Mishneh Torah", "Commentary", "Kessef Mishneh", old_categories[4]]
        new_dict = index.contents()
        new_dict["categories"] = new_categories
        index.load_from_dict(new_dict)
        index.save()


def post_avot_comm(title, book_text):
    send_text = {
        "text": book_text,
        "versionTitle": "ToratEmet",
        "versionSource": "http://www.toratemetfreeware.com/online/f_01313.html",
        "language": "he"
    }
    post_text(title, send_text, server="http://proto.sefaria.org")

if __name__ == "__main__":
    bartenura = {"name": "Bartenura on Pirkei Avot", "comment_marker": 'color:RGB<small><small>(72,119,170)</small></small>;',
                 "segment_marker": "color:RGB(45,104,176);", "he_name": u"ברטנורה"}
    rashi = {"name": "Rashi on Avot", "he_name": u"""רש"י""", "segment_marker": "color:RGB(45,104,176);",
             "comment_marker": 'color:RGB<small><small>(27,141,92)</small></small>;'}
    ikar_tyt = {"name": "Ikar Tosafot Yom Tov on Pirkei Avot", "he_name": u'עיקר תוי"ט', "comment_marker": "color:RGB<small><small>(51,119,204)</small></small>;", "segment_marker": "color:RGB(45,104,176);"}

    avot = Mishneh_Torah_Commentary("avot.html")

    for c in [ikar_tyt, bartenura, rashi]:
        avot.set_fields(he_name=c["he_name"], segment_marker=c["segment_marker"], comment_marker=c["comment_marker"], text={})
        avot.parse()
        post_avot_comm(c["name"], avot.text)

    '''
    rambam_sections = map(lambda x: library.get_index(x), library.get_indexes_in_category("Mishneh Torah"))
    hebrew_to_english = {rambam_section.get_title("he"): rambam_section.get_title("en") for rambam_section in rambam_sections}
    files = filter(lambda x: x.endswith(".html") and not x.startswith("errors"), os.listdir("."))
    maggid = {"name": "Maggid Mishneh", "segment_marker": 'color:RGB(45,104,176);', "comment_marker": 'color:RGB(122,13,134);', "he_name": u"מגיד משנה", "exclude": "madah.html"}
    lehem = {"name": "Lehem Mishneh", "segment_marker": 'color:RGB(45,104,176);', "comment_marker": "color:RGB(89,45,0);", "he_name": u"לחם משנה", "exclude": None}
    hasagot = {"name": "Hasagot HaRaavad", "comment_marker": 'color:RGB(15,74,172);', "segment_marker": 'color:RGB(45,104,176);', "he_name": u"""השגות הראב"ד""", "exclude": None}

    terms(maggid)
    terms(lehem)
    terms(hasagot)
    results = {}
    results["Maggid Mishneh"] = {}
    results["Lehem Mishneh"] = {}
    results["Hasagot HaRaavad"] = {}
    results["Peirush"] = {}

    #Parse peirush separately because it comments on only one section
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
        MTC = Mishneh_Torah_Commentary(file)

        for c in [maggid, lehem, hasagot]:
            if c["exclude"] == file:
                continue

            MTC.set_fields(he_name=c["he_name"], segment_marker=c["segment_marker"], comment_marker=c["comment_marker"], text={})
            MTC.parse()
            if MTC.text != {}:
                results[c["name"]].update(MTC.text)
                post_commentator(c, MTC.text, hebrew_to_english)
    '''