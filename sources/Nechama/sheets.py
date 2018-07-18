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





class Section(object):

    def __init__(self, letter, name):
        self.letter = letter
        self.name = name
        self.segments = []  # list of Segment objs


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
        self.pereks, self.pasuks = zip(*[self.ref.sections, self.ref.toSections])


class Qustion(object):

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


class Nechama_comment(object):

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

