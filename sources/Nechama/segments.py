#encoding=utf-8

from bs4 import BeautifulSoup, element
from sources.functions import getGematria
from sefaria.model.text import *



class Segments(object):

    def __init__(self, type):
        self.type = type


class Parshan(object):

    def __init__(self, section, segment_class, ref):
        self.parshan_name = u""
        self.about_parshan_ref = u""  # words of nechama in regards to the parshan or this specific book, that we will lose since it is not part of our "ref" system see 8.html sec 1. "shadal"
        self.perek = u""
        self.pasuk = u""
        self.ref = ref  # this can be blank indicating our parser couldn't figure out what the ref is
        self.nechama_comments = u""
        self.nechama_q = []  # list of Qustion objs about this Parshan seg
        self.section = section  # which section I belong to
        self.segment_class = segment_class

    def get_ref(self):
        return self.ref

    # def get_ref(self, segment, relevant_text):
    #     """uses the info we have from parshan segment to either get the most precise Sefaria Ref or conclude it isn't in the library"""
    #     pass
    # real_title, found_a_tag, a_tag_is_entire_comment, a_tag_in_long_comment \
    #     = self.get_a_tag_from_ref(segment, relevant_text)
    #
    # is_perek_pasuk_ref, real_title, found_ref_in_string \
    #     = self.check_ref_and_add_to_quotation_stack(next_segment_class, relevant_text, real_title)
    #
    # combined_with_prev_line = set_ref_segment(combined_with_prev_line)

    def add_text(self, orig_text, segment_class, pre_text=""):
        self.text = orig_text
        self.pre_text = pre_text
        self.parshan_name = segment_class
        if self.section.last_comm_index_not_found_bool:
            if self.last_comm_index_not_found not in self.section.sheet.index_not_found.keys():
                self.section.sheet.index_not_found[self.last_comm_index_not_found] = []
            self.section.sheet.index_not_found[self.last_comm_index_not_found].append(
                (self.section.current_parsha_ref, orig))
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
        self.section = section
        table_html = str(segment)
        table_html = self.section.remove_hyper_links(table_html)
        formatted_text = self.format(BeautifulSoup(table_html, "lxml").text)
        self.text = u"<table><tr><td><big>{}</big></td></tr></table>".format(formatted_text)

    @staticmethod
    def is_header(segment):
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

    def __init__(self, section, segment):
        self.number = None
        self.letter = None
        self.difficulty = 0
        self.section = section
        table_html = str(segment)
        table_html = self.section.remove_hyper_links(table_html)
        self.text = self.format(table_html)

    @staticmethod
    def is_question(segment):
        return isinstance(segment, element.Tag) and segment.name == "table" and \
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

    def __init__(self, section, segment):
        self.section = section
        self.text = str(segment)

    @staticmethod
    def is_table(segment):
        return segment.attrs.get("class", "") in [["RT"], ["RTBorder"]]


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

