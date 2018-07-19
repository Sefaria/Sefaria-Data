#encoding=utf-8

import django
django.setup()

import requests
import re
import os
from bs4 import BeautifulSoup, element
from sources.functions import getGematria
from sefaria.model import *
from sefaria.model.text import *
from collections import OrderedDict


class Sheet(object):

    def __init__(self, html, parasha, title, year, ref=None):
        self.html = html
        self.title = title
        self.parasha = parasha
        self.he_year = re.sub(u"שנת", u"", year).strip()
        self.year = getGematria(self.he_year)+5000  # +1240, jewish year is more accurate
        self.sections = []
        self.pesukim = self.get_ref(ref)  # (re.sub(u"(פרק(ים)?|פסוק(ים)?)", u"", ref).strip())
        self.sheet_remark = u""
        self.header_links = None  # this will link to other  nechama sheets (if referred).
        self.quotations = [] #last one in this list is the current ref
        self.current_parsha_ref = ""

    def get_ref(self, he_ref):
        # he_ref = re.sub(u"(פרק(ים)?|פסוק(ים)?)", u"", he_ref).strip()
        # split = re.split()
        try:
            r = Ref(he_ref)
            print r.normal()
        except InputError:
            print 'InputError'
            return None
        return r

    def parse_as_text(self, text):
        sheet_sections = []
        intro_segment = intro_tuple = None
        for div in text.find_all("div"):
            if div['id'] == "sheetRemark" and div.text.replace(" ","") != "":  # comment of hers that appears at beginning of section
                # refs_to_other_sheets = self.get_links_to_other_sheets(div)
                intro_segment = div
                intro_tuple = ("nechama", "<b>" + intro_segment.text + "</b>", "")
            elif "ContentSection" in div['id']:  # sections within source sheets
                self.current_section += 1
                new_section = Section(self.current_section)
                self.sections.append()
                assert str(self.current_section) in div['id']

                if div.text.replace(" ", "") == "":
                    continue

                # removes nodes with no content
                segments = new_section.get_children_with_content(div)

                # blockquote is really just its children so get replace it with them
                # and tables  need to be handled recursively
                segments = new_section.check_for_blockquote_and_table(segments, level=2)

                # here is the main logic of parsing

                segments = new_section.classify_segments(segments)
                self.RT_Rashi = False
                if intro_segment:
                    segments.insert(0, intro_tuple)
                    intro_segment = None

                # assert len(self.quotations) == self.current_pos_in_quotation_stack+1
                # assert 3 > len(self.quotation_stack) > 0
                # if len(self.quotation_stack) >= 2:
                #    segments = self.add_links_from_intro_to_many_comments(segments)
                self.quotations = [["bible", self.quotation_stack[0]]]
                sheet_sections.append(segments)
        return sheet_sections




class Segments(object):

    def __init__(self, type):
        self.type = type


class Parshan(object):

    def __init__(self, section):
        self.parshan_name = u""
        self.about_parshan_ref = u"" #words of nechama in regards to the parshan or this specific book, that we will lose since it is not part of our "ref" system see 8.html sec 1. "shadal"
        self.perek = u""
        self.pasuk = u""
        self.ref = self.get_ref()
        self.nechama_comments = u""
        self.nechama_q = [] #list of Qustion objs about this Parshan seg
        self.section = None #which section I belong to

    def get_ref(self):
        """uses the info we have from parshan segment to eather get the most precise Sefaria Ref or conclude it isn't in the library"""
        ref = None
        return ref

    def add_text(self, orig_text, segment_class, pre_text=""):
        self.text = orig_text
        self.pre_text = pre_text
        self.parshan_name = segment_class
        if self.section.last_comm_index_not_found_bool:
            if self.last_comm_index_not_found not in self.section.sheet.index_not_found.keys():
                self.section.sheet.index_not_found[self.last_comm_index_not_found] = []
            self.section.sheet.index_not_found[self.last_comm_index_not_found].append((self.section.current_parsha_ref, orig))
            self.last_comm_index_not_found = None
            self.last_comm_index_not_found_bool = False
        elif segment_class in self.section.sheet.important_classes:
            quote = self.section.quotations[-1]
            category, ref = quote
            self.ref = ref
        else:
            self.section.sheet.add_to_table_classes(segment_class)

class Bible(object):

    def __init__(self, pasuk_ref):
        self.ref = Ref(pasuk_ref)


class Header(object):
    def __init__(self, section, segment):
        table_html = str(segment)
        table_html = self.section.remove_hyper_links(table_html)
        formatted_text = self.format(BeautifulSoup(table_html, "lxml").text)
        self.text = u"<table><tr><td><big>{}</big></td></tr></table>".format(formatted_text)
        self.section = section

    @staticmethod
    def is_header(self, segment):
        return isinstance(segment, element.Tag) and segment.name == "table" and \
               segment.attrs["class"][0] in ["header"]

    def format(self, comment):
        found_difficult = ""
        # digits = re.findall("\d+\.", comment)
        # for digit in set(digits):
        #     comment = comment.replace(digit, "<b>"+digit + " </b>")
        if "pages/images/hard.gif" in comment:
            found_difficult += "*"
        if "pages/images/harder.gif" in comment:
            found_difficult += "*"

        #we need to specifically keep these tags because the "text" property will remove them so we "hide" them with nosense characters
        tags_to_keep = ["u", "b"]
        comment = comment.replace("<u>", "$!u$").replace("</u>", "$/!u$")
        comment = comment.replace("<b>", "$!b$").replace("</b>", "$/!b$")
        text = BeautifulSoup(comment, "lxml").text

        text = text.strip()
        while "  " in text:
            text = text.replace("  ", " ")

        #following code makes sure "3.\nhello" becomes "3. hello"
        digit = re.match(u"^.{1,2}[\)|\.]", text)
        if digit:
            text = text.replace(digit.group(0), u"")
            text = text.strip()
            text = digit.group(0) + u" " + text

        # now get the tags back and remove nonsense chars
        text = text.replace("$!u$", "<u>").replace("$/!u$", "</u>")
        text = text.replace("$!b$", "<b>").replace("$/!b$", "</b>")
        text = text.replace("\n", "<br/>")

        return (found_difficult + text).strip()

class Question(object):

    def __init__(self, section, segment):
        self.number = None
        self.letter = None
        self.difficulty = 0
        table_html = str(segment)
        table_html = self.section.remove_hyper_links(table_html)
        self.text = self.format(table_html)

    @staticmethod
    def is_question(self, segment):
        return isinstance(segment, element.Tag) and segment.name == "table" and\
               segment.attrs["class"][0] in ["question", "question2"]

    def format(self, comment):
        found_difficult = ""
        # digits = re.findall("\d+\.", comment)
        # for digit in set(digits):
        #     comment = comment.replace(digit, "<b>"+digit + " </b>")
        if "pages/images/hard.gif" in comment:
            found_difficult += "*"
        if "pages/images/harder.gif" in comment:
            found_difficult += "*"

        #we need to specifically keep these tags because the "text" property will remove them so we "hide" them with nosense characters
        tags_to_keep = ["u", "b"]
        comment = comment.replace("<u>", "$!u$").replace("</u>", "$/!u$")
        comment = comment.replace("<b>", "$!b$").replace("</b>", "$/!b$")
        text = BeautifulSoup(comment, "lxml").text

        text = text.strip()
        while "  " in text:
            text = text.replace("  ", " ")

        #following code makes sure "3.\nhello" becomes "3. hello"
        digit = re.match(u"^.{1,2}[\)|\.]", text)
        if digit:
            text = text.replace(digit.group(0), u"")
            text = text.strip()
            text = digit.group(0) + u" " + text

        # now get the tags back and remove nonsense chars
        text = text.replace("$!u$", "<u>").replace("$/!u$", "</u>")
        text = text.replace("$!b$", "<b>").replace("$/!b$", "</b>")
        text = text.replace("\n", "<br/>")

        return (found_difficult + text).strip()

class Table(object):

    def __init__(self):
        pass

class RT_Rashi(object):

    """an object representing an RT_Rashi table for parsing purposes"""


class Nechama_Comment(object):

    def __init__(self, text):
        self.text = text


def bs4_reader(file_list_names):
    """
    The main BeautifulSoup reader function, that etrates on all sheets and creates the obj, probably should be in it's own file
    :param self:
    :return:
    """
    sheets = OrderedDict()
    for html_sheet in file_list_names:
        content = BeautifulSoup(open("{}".format(html_sheet)), "lxml")
        print html_sheet
        top_dict = dict_from_html_attrs(content.find('div', {'id': "contentTop"}).contents)
        # print 'len_content type ', len(top_dict.keys())
        sheet = Sheet(html_sheet, top_dict["paging"].text, top_dict["h1"].text, top_dict["year"].text, top_dict["pasuk"].text)
        sheets[html_sheet] = sheet
        body_dict = dict_from_html_attrs(content.find('div', {'id': "contentBody"}))
        sheet.sections.extend([v for k, v in body_dict.items() if re.search(u'ContentSection_\d', k)]) # check that these come in in the right order
        sheet.sheet_remark = body_dict['sheetRemark'].text

        pass
    return sheets

    # for which_sheet, i in enumerate(self.bereshit_parshiot):
    #     i += ".html"
    #     self.sheet_num = which_sheet + 1
    #     content = BeautifulSoup(open("{}".format(i)), "lxml")
    #     header = content.find('div', {'id': 'contentTop'})
    #     if page_missing in header.text:
    #         continue
    #     sheet_title = header.find("h1").text
    #     hebrew_year = content.find("div", {"id": "year"}).text.replace(u"שנת", u"")
    #     roman_year = getGematria(hebrew_year) + 1240
    #     self.current_en_year = roman_year
    #
    #     parsha = content.find("div", {"id": "paging"}).text
    #     self.current_parsha = parsha
    #     print i
    #     self.current_sefer, self.current_perakim, self.current_pasukim = self.extract_perek_info(content)
    #     self.current_sefer = library.get_index(self.current_sefer)
    #     self.current_alt_titles = self.current_sefer.nodes.get_titles('en')
    #     self.current_sefer = self.current_sefer.title
    #     text = content.find("div", {"id": "contentBody"})
    #     if parsha not in self.sheets:
    #         self.sheets[parsha] = {}
    #     assert roman_year not in self.sheets[parsha].keys()
    #     self.year_to_url[roman_year] = i
    #     self.year_to_sheet[roman_year] = sheet_title
    #     self.current_url = i
    #     self.current_perek = self.current_perakim[0]
    #     self.current_pasuk = None
    #     self.quotations = []
    #     self.current_pos_in_quotation_stack = 0
    #     self.quotation_stack = []
    #     self.current_section = 0
    #     self.quotation_stack = []
    #     self.current_parsha_ref = ["bible", u"{} {}".format(self.current_sefer, self.current_perek)]
    #     self.add_to_quotation_stack(self.current_parsha_ref)
    #     self.sheets[parsha][self.current_en_year] = (
    #     self.current_url, hebrew_year, self.current_sefer, self.current_perakim, self.parse_as_text(text))
    #     self.post_text(parsha, self.current_en_year, self.sheets[parsha][self.current_en_year])

def dict_from_html_attrs(contents):
    d = OrderedDict()
    for e in [e for e in contents if isinstance(e, element.Tag)]:
        if "id" in e.attrs.keys():
            d[e.attrs['id']] = e
        else:
            d[e.name] = e
    return d


if __name__ == "__main__":
    # Ref(u"בראשית פרק ג פסוק ד - פרק ה פסוק י")
    # Ref(u"u'דברים פרק ט, ז-כט - פרק י, א-י'")
    # sheets = bs4_reader(['html_sheets/{}.html'.format(x) for x in ["1", "2", "30", "62", "84", "148","212","274","302","378","451","488","527","563","570","581","750","787","820","844","894","929","1021","1034","1125","1183","1229","1291","1351","1420"]])
    sheets = bs4_reader(["html_sheets/{}".format(fn) for fn in os.listdir("html_sheets") if fn != 'errors.html'])
    pass

