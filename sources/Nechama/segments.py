#encoding=utf-8

from bs4 import BeautifulSoup, element
from sources.functions import getGematria
from sefaria.model.text import *
from main import *


class Segment(object):

    def __init__(self, type):
        self.type = type
        self.text = ""

    def create_source(self):
        #create source for sourcesheet out of myself
        source = {"outsideText": self.text}
        return source



class Source(object):

    def __init__(self, segment_class, ref):
        self.parshan_name = u""
        self.about_source_ref = u""  # words of nechama in regards to the parshan or this specific book, that we will lose since it is not part of our "ref" system see 8.html sec 1. "shadal"
        self.perek = u""
        self.pasuk = u""
        self.ref = ref  # this can be blank indicating our parser couldn't figure out what the ref is
        self.nechama_comments = u""
        self.nechama_q = []  # list of Qustion objs about this Parshan seg
        self.segment_class = segment_class
        self.text = u""


    @staticmethod
    def is_source_text(segment, important_classes):
        return isinstance(segment, element.Tag) and "class" in segment.attrs.keys() and segment.attrs["class"][0] in important_classes

    def get_sefaria_ref(self, ref):
        if ref == "":
            return None
        try:
            r = Ref(ref)
            assert r.text('he').text
            return r
        except (InputError,  AssertionError) as e:
            #try to see if all that is wrong is the segment part of the ref, say, for Ralbag Beur HaMilot on Torah, Genesis 4:17
            last_part = self.ref.split()[-1]
            if last_part[0].isdigit(): # in format, Ralbag Beur HaMilot on Torah, Genesis 4:17 and last_part is "4:17", now get the node "Ralbag Beur HaMilot on Torah, Genesis"
                ref_node = " ".join(self.ref.split(" ")[0:-1])
                return self.get_sefaria_ref(ref_node) #returns Ralbag Beur HaMilot on Torah, Genesis
            else:
                return None

    def glue_ref_and_text(self, ref, text):
        return u"<small><b>{}</b><br/>{}</small>".format(ref, text)

    def create_source(self):
        #create source for sourcesheet out of myself
        comment = self.text
        # is Sefaria ref
        if self.get_sefaria_ref(self.ref):
            if self.about_source_ref:
                comment = self.glue_ref_and_text(self.about_source_ref, comment)
            enRef = Ref(self.ref).normal()
            heRef = Ref(self.ref).he_normal()
            source = {"ref": enRef, "heRef": heRef,
                      "text":
                          {
                              "he": comment,
                              "en": ""
                          },
                      "options": {
                          "indented": "indented-1",
                          "sourceLayout": "",
                          "sourceLanguage": "hebrew",
                          "sourceLangLayout": ""
                      }
                      }
        elif self.ref:  # thought we found a ref but it's not an actual ref in sefaria library
            if self.about_source_ref:
                comment = self.glue_ref_and_text(self.about_source_ref, comment) #use actual text if we can
            else:
                comment = self.glue_ref_and_text(self.ref, comment) # otherwise, use the ref we thought it was

            source = {"outsideText": comment,
                      "options": {
                          "indented": "indented-1",
                          "sourceLayout": "",
                          "sourceLanguage": "hebrew",
                          "sourceLangLayout": ""
                      }
                      }
        elif not self.ref and self.about_source_ref:
            comment = self.glue_ref_and_text(self.about_source_ref, comment)
            source = {"outsideText": comment,
                      "options": {
                          "indented": "indented-1",
                          "sourceLayout": "",
                          "sourceLanguage": "hebrew",
                          "sourceLangLayout": ""
                        }
                      }
        else:
            raise InputError, "Didn't anticipate this case in the casses of ref on Source obj"
        return source



    def get_ref(self):
        return self.ref


    def add_text(self, segment, segment_class):
        segment_text = segment.text.replace("\n", "").replace("\r", "")
        self.parshan_name = segment_class
        if not self.text:
            self.text = segment_text
            return self
        else:
            new_source = self.copy()
            new_source.text = segment_text
            return new_source



    def index_not_found(self):
        return not self.get_ref() and self.about_source_ref #not found a ref, but have info on what it is


    def copy(self):
        # ref_copy = Ref(self.ref.normal())
        ref_copy = self.ref
        new_source = Source(self.segment_class, ref_copy)
        new_source.parshan_name = self.parshan_name
        # new_source.pasuk = self.pasuk
        # new_source.perek = self..perek

        return new_source

class Header(object):
    def __init__(self, segment):
        table_html = str(segment)
        formatted_text = self.format(BeautifulSoup(table_html, "lxml").text)
        self.text = u"<table><tr><td><big>{}</big></td></tr></table>".format(formatted_text)

    @staticmethod
    def is_header(segment):
        return isinstance(segment, element.Tag) and segment.name == "table" and \
               segment.attrs["class"][0] in ["header"]

    def create_source(self):
        #create source for sourcesheet out of myself
        source = {"outsideText": self.text}
        return source

    def format(self, comment):
        found_difficult = ""
        # digits = re.findall("\d+\.", comment)
        # for digit in set(digits):
        #     comment = comment.replace(digit, "<b>"+digit + " </b>")

        all_a_links = re.findall("(<a href.*?>(.*?)</a>)", comment)
        for a_link_and_text in all_a_links:
            a_link, text = a_link_and_text
            comment = comment.replace(a_link, text)

        if "pages/images/hard.gif" in comment:
            found_difficult += "*"
        if "pages/images/harder.gif" in comment:
            found_difficult += "*"

        # we need to specifically keep these tags because the "text" property will remove them so we "hide" them with nosense characters
        tags_to_keep = ["u", "b"]
        comment = comment.replace("<u>", "$!u$").replace("</u>", "$/!u$")
        comment = comment.replace("<b>", "$!b$").replace("</b>", "$/!b$")
        text = BeautifulSoup(comment, "lxml").text

        text = text.strip()
        while "  " in text:
            text = text.replace("  ", " ")

        # following code makes sure "3.\nhello" becomes "3. hello"
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

    def __init__(self, segment):
        self.number = None
        self.letter = None
        self.difficulty = 0
        table_html = str(segment)
        self.text = self.format(table_html)

    @staticmethod
    def is_question(segment):
        return isinstance(segment, element.Tag) and segment.name == "table" and \
               segment.attrs["class"][0] in ["question", "question2"]

    def create_source(self):
        #create source for sourcesheet out of myself
        source = {"outsideText": self.text}
        return source

    def format(self, comment):
        found_difficult = ""
        # digits = re.findall("\d+\.", comment)
        # for digit in set(digits):
        #     comment = comment.replace(digit, "<b>"+digit + " </b>")
        all_a_links = re.findall("(<a href.*?>(.*?)</a>)", comment)
        for a_link_and_text in all_a_links:
            a_link, text = a_link_and_text
            comment = comment.replace(a_link, text)

        if "pages/images/hard.gif" in comment:
            found_difficult += "*"
        if "pages/images/harder.gif" in comment:
            found_difficult += "**"

        # we need to specifically keep these tags because the "text" property will remove them so we "hide" them with nosense characters
        tags_to_keep = ["u", "b"]
        comment = comment.replace("<u>", "$!u$").replace("</u>", "$/!u$")
        comment = comment.replace("<b>", "$!b$").replace("</b>", "$/!b$")
        text = BeautifulSoup(comment, "lxml").text

        text = text.strip()
        while "  " in text:
            text = text.replace("  ", " ")

        # following code makes sure "3.\nhello" becomes "3. hello"
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
    ## specifically for tables in HTML that end up staying as HTML in source sheet such class="RT" or "RTBorder"

    def __init__(self, segment):
        self.text = str(segment)

    @staticmethod
    def is_table(segment):
        return isinstance(segment, element.Tag) and segment.attrs.get("class", "") in [["RT"], ["RTBorder"]]

    def create_source(self):
        #create source for sourcesheet out of myself
        source = {"outsideText": self.text}
        return source


class RT_Rashi(object):
    """an object representing an RT_Rashi table for parsing purposes"""


class Nechama_Comment(object):

    def __init__(self, text):
        self.text = text

    @staticmethod
    def is_comment(segments, i, important_classes):
        # determine if it's worth looking to see what this ref is:
        # if it's the last one, it's not a ref because a comment needs to come after it
        # if the next one isn't a Tag, this can't be a ref because comments are always Tags with classes
        # indicating parshan, bible, etc.
        # also make sure the next one has a class in self.important_classes
        # if it doesn't meet all the criteria, then it's just a comment by Nechama
        segment = segments[i]
        next_comment_parshan_or_bible = ""
        this_comment_could_be_ref = i < len(segments) - 1 and isinstance(segments[i + 1], element.Tag) and isinstance(
            segments[i], element.Tag)
        if this_comment_could_be_ref:
            next_comment_parshan_or_bible = "class" in segments[i + 1].attrs.keys() and \
                                            segments[i + 1].attrs["class"][0] in important_classes
        return not next_comment_parshan_or_bible or not this_comment_could_be_ref



    def create_source(self):
        #create source for sourcesheet out of myself
        source = {"outsideText": self.text}
        return source