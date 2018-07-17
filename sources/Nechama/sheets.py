#encoding=utf-8

import django
django.setup()

import requests
import re
from bs4 import BeautifulSoup, element
from sources.functions import getGematria
from sefaria.model import *
from sefaria.model.text import *


class Sheet(object):

    def __init__(self, title, year, ref):
        self.title = title
        self.year = getGematria(year)+1240
        self.he_year = year
        self.sections = []
        self.pesukim = Ref(ref)
        self.header_text = u""
        self.header_links = None  # this will link to other  nechama sheets (if referred).


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


class Tanakh_extract(object):

    def __init__(self, pasuk_ref):
        self.ref = Ref(pasuk_ref)
        self.pereks, self.pasuks = zip(*[self.ref.sections, self.ref.toSections])


class Qustion(object):

    def __init__(self, number):
        self.number = None
        self.letter = None
        self.difficulty = 0
        self.text = u""


def bs4_reader(self):
    """
    The main BeautifulSoup reader function, that etrates on all sheets and creates the obj, probably should be in it's own file
    :param self:
    :return:
    """
    pass



