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
                self.quotation_stack = [u"{} {}".format(self.current_sefer, section.current_perek)]
                self.quotations = [["bible", self.quotation_stack[0]]]
                sheet_sections.append(segments)
        return sheet_sections



class Section(object):

    def __init__(self):
        self.letter = ""
        self.name = ""
        self.segments = []  # list of Segment objs
        self.first_bible_ref = "" # used to link everything below it

    def relevant_text(self, segment):
        if isinstance(segment, element.Tag):
            return segment.text
        return segment


    def find_all_p(self, segment):
        def skip_p(p):
            text_is_unicode_space = lambda x: len(x) <= 2 and (chr(194) in x or chr(160) in x)
            no_text = p.text == "" or p.text == "\n" or p.text.replace(" ", "") == "" or text_is_unicode_space(
                p.text.encode('utf-8'))
            return no_text and not p.find("img")

        ps = segment.find_all("p")
        new_ps = []
        temp_p = ""
        for p_n, p in enumerate(ps):
            if skip_p(p):
                continue
            elif len(p.text.split()) == 1 and re.compile(u"^.{1,2}[\)|\.]").match(p.text):  # make sure it's in form 1. or ש.
                temp_p += p.text
            elif p.find("img"):
                img = p.find("img")
                if "pages/images/hard.gif" == img.attrs["src"]:
                    temp_p += "*"
                elif "pages/images/harder.gif" == img.attrs["src"]:
                    temp_p += "**"
            else:
                if temp_p:
                    temp_tag = BeautifulSoup("<p></p>", "lxml")
                    temp_tag = temp_tag.new_tag("p")
                    temp_tag.string = temp_p
                    temp_p = ""
                    p.insert(0, temp_tag)
                new_ps.append(p)

        return new_ps

    def get_children_with_content(self, segment):
        # determine if the text of segment is blank or practically blank (i.e. just a \n or :\n\r) or is just empty space less than 3 chars
        children_w_contents = [el for el in segment.contents if self.relevant_text(el).replace("\n", "").replace("\r", "").replace(": ", "").replace(":", "") != "" and len(self.relevant_text(el)) > 2]
        return children_w_contents

    def check_for_blockquote_and_table(self, segments, level=2):
        new_segments = []
        tables = ["table", "tr"]
        for i, segment in enumerate(segments):
            if isinstance(segment, element.Tag):
                class_ = segment.attrs.get("class", [""])[0]
            else:
                new_segments.append(segment)
                continue
            if segment.name == "blockquote":  # this is really many children so add them to list
                new_segments += self.get_children_with_content(segment)
            elif segment.name == "table":
                if segment.name == "table":
                    if class_ == "header" or class_ == "RTBorder" or class_ == "RT":
                        new_segments.append(segment)
                    elif class_ == "RT_RASHI":
                        new_segments += self.find_all_p(segment)
                        self.RT_Rashi = True
                    elif class_ in ["question", "question2"]:
                        # question_in_question = [child for child in segment.descendants if
                        #                   child.name == "table" and child.attrs["class"][0] in ["question", "question2"]]
                        # RT_in_question = [child for child in segment.descendants if
                        #                   child.name == "table" and child.attrs["class"][0] in ["RT", "RTBorder"]]
                        new_segments.append(segment)
            else:
                # no significant class and not blockquote or table
                new_segments.append(segment)

        level -= 1
        if level > -1:  # go level deeper unless level isn't > 0
            new_segments = self.check_for_blockquote_and_table(new_segments, level)
        return new_segments

    def remove_hyper_links(self, html):
        all_a_links = re.findall("(<a href.*?>(.*?)</a>)", html)
        for a_link_and_text in all_a_links:
            a_link, text = a_link_and_text
            html = html.replace(a_link, text)
        return html

    def process_table(self, segments, i):
        formatted_text = ""
        segment = segments[i]
        table_html = str(segment)
        table_html = self.remove_hyper_links(table_html)

        if segment.attrs['class'] in [["question2"], ["question"]]:
            table_html = self.format(table_html)
            formatted_text = self.format(BeautifulSoup(table_html, "lxml").text)
        elif segment.attrs['class'] in [["header"]]:
            formatted_text = self.format(BeautifulSoup(table_html, "lxml").text)
            formatted_text = u"<table><tr><td><big>{}</big></td></tr></table>".format(formatted_text)
        segments[i] = ("nechama", formatted_text, "")


    def process_comment_specific_class(self, segments, i, formatted, orig, segment_class):
        if self.last_comm_index_not_found:
            if type(self.last_comm_index_not_found) is not bool:  # set to True when couldn't find anything but don't even have a_tag
                if self.last_comm_index_not_found not in self.index_not_found.keys():
                    self.index_not_found[self.last_comm_index_not_found] = []
                self.index_not_found[self.last_comm_index_not_found].append((self.current_parsha_ref, orig))
            self.last_comm_index_not_found = None
            segments[i] = (segment_class, orig, formatted, "")
        elif segment_class in self.important_classes:
            quote = self.quotations[-1]
            category, ref = quote
            segments[i] = (segment_class, orig, formatted, ref)
        else:
            self.add_to_table_classes(segment_class)


class Segments(object):

    def __init__(self, type):
        self.type = type


class Parshan(object):

    def __init__(self):
        self.parshan_name = u""
        self.about_parshan_ref = u"" #words of nechama in regards to the parshan or this specific book, that we will lose since it is not part of our "ref" system see 8.html sec 1. "shadal"
        self.perek = u""
        self.pasuk = u""
        self.ref = self.get_ref()
        self.nechama_comments = u""
        self.nechama_q = [] #list of Qustion objs about this Parshan seg


    def get_ref(self):
        """uses the info we have from parshan segment to eather get the most precise Sefaria Ref or conclude it isn't in the library"""
        ref = None
        return ref


class Bible(object):

    def __init__(self, pasuk_ref):
        self.ref = Ref(pasuk_ref)


class Question(object):

    def __init__(self, number):
        self.number = None
        self.letter = None
        self.difficulty = 0
        self.text = u""


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

