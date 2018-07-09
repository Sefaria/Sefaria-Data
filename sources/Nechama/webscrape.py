#encoding=utf-8
import requests
import re
from bs4 import BeautifulSoup, element
from sources.functions import getGematria
import logging
import bleach
logger = logging.getLogger(__name__)
import django
import bleach
import os
from sefaria.system.database import db
from research.source_sheet_disambiguator.main import refine_ref_by_text

django.setup()
from sources.functions import UnicodeWriter
import urllib2, urllib
from sefaria.model import *
from sefaria.system.exceptions import *
from sources.functions import convertDictToArray, post_index, post_text, post_link, post_sheet
import difflib
from collections import Counter
import time
from sefaria.model.schema import AddressYear, AddressInteger
from data_utilities.util import WeightedLevenshtein
from sefaria.system.exceptions import *
from sources.functions import UnicodeWriter, UnicodeReader

class Sheets:
    def __init__(self):
        self.he_title_project = u"גיליונות נחמה"
        self.en_title_project = "Nechama Leibowitz Source Sheets"
        self.versionTitle = "asdf"
        self.versionSource = "http://nechama.sandbox.sefaria.org"
        self.table_classes = {}
        self.server = self.versionSource
        self.important_classes = ["parshan", "midrash", "talmud", "bible", "commentary"]
        self.bereshit_parshiot = ["1", "2", "30", "62", "84", "148","212","274","302","378","451","488","527","563","570","581","750","787","820","844","894","929","1021","1034","1125","1183","1229","1291","1351","1420"]
        self.sheets = {}
        self.links = []
        self.current_pos_in_quotation_stack = -1
        self.current_section = 0
        self.current_url = ""
        self.current_perek = 1
        self.current_perakim = []
        self.year_to_url = {}
        self.current_pasuk = None
        self.current_parsha_ref = None
        self.current_sefer = ""
        self._term_cache = {} # used so we don't have to look up "Rashi" in database over and over
        self.current_parsha = ""
        self.current_en_year = ""
        self.year_to_sheet = {}
        self.sheet_num = 0 #corresponds to nechama.sandbox.sefaria.org/sheets/sheet_num
        #these two variables keep track of layers of quotations Nechama references...quotations is a list of all quotations
        #and quotation_stack is a stack that we pop when we find a quotation in quotations
        #then we can check the stack later to see if there were any quoations that weren't popped/used
        self.quotations = []
        self.quotation_stack = []
        self.current_ref_in_sefaria = None #when she mentions a ref, what text does the ref correspond to in Sefaria library?


        self.found = set() #found holds all titles of books we found in the library
        self.ref_not_found = Counter()
        self.last_comm_index_not_found = False
        reader = UnicodeReader(open("index_not_found.csv"))
        self.index_not_found = Counter() #indexes not found in library
        for row in reader:
            self.index_not_found[row[0]] += 1
        self.index_not_found_csv = UnicodeWriter(open("index_not_found.csv", 'a'))
        self.intro_to_many_comment_finds = Counter() #2.html 5th section Shadal
        self.significant_class = lambda class_: True#"question" in class_ #class_ in ["header", "question"] or "question" in class_
        self.RT_Rashi = False
        self.term_mapping = {
            u"תנחומא": u"Midrash Tanchuma, Bereshit",
            u"בעל גור אריה": u"Gur Aryeh on Bereishit",
            u"""ראב"ע""": u"Ibn Ezra on Genesis",
            u"""וראב"ע:""": u"Ibn Ezra on Genesis",
            u"עקדת יצחק": u"Akeidat Yitzchak",
            u"תרגום אונקלוס": u"Onkelos Genesis",
            u"""רלב"ג""": u"Ralbag Beur HaMilot on Torah, Genesis",
            u"""רמב"ם""": u"Guide for the Perplexed",
            u"ר' אליהו מזרחי": u"Mizrachi, Genesis",
            u"""ר' יוסף בכור שור""": u"Bekhor Shor, Genesis",
            u"אברבנאל": u"Abarbanel on Torah, Genesis",
            u"""המלבי"ם""": u"Malbim on Genesis",
            u"משך חכמה": u"Meshech Hochma, Bereshit",
            u"רבנו בחיי": u"Rabbeinu Bahya, Bereshit",
            u'רב סעדיה גאון': u"Saadia Gaon on Genesis"

        }
        self.doesnt_match = {}
        self.good_match = 0
        self.fixed_match = 0
        self.refs_to_nowhere = {}


    def relevant_text(self, segment):
        if isinstance(segment, element.Tag):
            return segment.text
        return segment

    def get_links_to_other_sheets(self, div):
        a_tags = div.find_all("a")
        for link in [el.text for el in a_tags]:
            #create URL based on link_text: Currently it's Hebrew equivalent of "Bereshit 1942"
            if len(link.split()) == 2:
                parsha, year = link.split()
            elif len(link.split()) == 1:
                parsha = self.current_parsha
                year = link
            he_year_as_num = AddressYear.toNumber("he", year)
            en_year = AddressYear.toStr("en", he_year_as_num)
            other_source_sheet = u"{} {} {}".format(self.en_title_project, parsha, en_year)
            this_source_sheet = u"{} {} {}:1".format(self.en_title_project, self.current_parsha, self.current_en_year)
            link = {
                    "refs": [other_source_sheet, this_source_sheet],
                    "type": "commentary",
                    "auto": True,
                    "generated_by": "nechama_linker"
                  }
            self.links.append(link)


    def parse_as_sheets(self, text):
        pass


    def parse_as_text(self, text):
        sheet_sections = []
        intro_segment = intro_tuple = None
        for div in text.find_all("div"):
            if div['id'] == "sheetRemark" and div.text.replace(" ", "") != "": # comment of hers that appears at beginning of section
                #refs_to_other_sheets = self.get_links_to_other_sheets(div)
                intro_segment = div
                intro_tuple = ("nechama", "<b>" + intro_segment.text + "</b>", "")
            elif "ContentSection" in div['id']: #sections within source sheets
                self.current_section += 1
                assert str(self.current_section) in div['id']

                if div.text.replace(" ", "") == "":
                    continue

                # removes nodes with no content
                segments = self.get_children_with_content(div)

                # blockquote is really just its children so get replace it with them
                # and tables  need to be handled recursively
                segments = self.check_for_blockquote_and_table(segments, level=2)

                # here is the main logic of parsing

                segments = self.classify_segments(segments)
                self.RT_Rashi = False
                if intro_segment:
                    segments.insert(0, intro_tuple)
                    intro_segment = None

                #assert len(self.quotations) == self.current_pos_in_quotation_stack+1
                #assert 3 > len(self.quotation_stack) > 0
                #if len(self.quotation_stack) >= 2:
                #    segments = self.add_links_from_intro_to_many_comments(segments)
                self.quotation_stack = [u"{} {}".format(self.current_sefer, self.current_perek)]
                self.quotations = [["bible", self.quotation_stack[0]]]
                sheet_sections.append(segments)
        return sheet_sections


    def add_links_from_intro_to_many_comments(self, segments):
        # this should only happen when there was a comment about a commentator
        # that introduced other comments
        # so that we have multiple layers of depth -- not only does each comment get linked
        # as normal, but they should all link to the original comment's commentator
        special_segment = None
        special_segs_found = 0
        for i, segment in enumerate(segments):
            # check each segment to see if it's in intro_to_many_comment_finds
            # if it is, everything below should be linked accordingly
            # UNTIL we find ANOTHER segment that is intro_to_many_comment_finds
            # in which case everything below it should be linked accordingly
            if segment in self.intro_to_many_comment_finds.keys():
                assert segment[2] in self.quotation_stack
                special_segment = segment
                special_segs_found += 1
            elif special_segment and segment[0] != "combined_with_next_line":
                # add add_link_from_segment's link to each segment after it
                segments[i] = list(segments[i])
                segments[i][2] += u"|{}".format(special_segment[2])
                segments[i] = tuple(segments[i])
        assert special_segs_found == len(self.intro_to_many_comment_finds)
        self.intro_to_many_comment_finds = Counter()
        return segments

    def question_inside_question(self, segment):
        def pass_td_test(element):
            if type(element) is element.NavigableString:
                return False
            tds_with_no_class = [el for el in element.contents if el.name == "td" and el.attrs.get("class") is None]
            if len(tds_with_no_class) != 1:
                return False

            td_bullet = [el for el in element.contents if el.name == "td" and el.attrs.get("class")
                         and el.attrs["class"] == ["border"]]
            td_number = [el for el in element.contents if el.name == "td" and el.attrs.get("class")
                         and el.attrs["class"] == ["number"]]
            if not td_bullet and not td_number:
                return False

            return True

        #Check that bullet or number exist and only ONE td with no class

        contents = segment.find_all("td")
        [pass_td_test(content) for content in contents]


#logic is if it's a header don't even count it; if it's not question or header, count it; if it's a question with tables below it, don't count it

    def check_for_blockquote_and_table(self, segments, level=2):
        def skip_p(p):
            text_is_unicode_space = lambda x: len(x) <= 2 and (chr(194) in x or chr(160) in x)
            no_text = p.text == "" or p.text == "\n" or p.text.replace(" ", "") == "" or text_is_unicode_space(p.text.encode('utf-8'))
            return no_text and not p.find("img")

        def find_all_p(segment):
            ps = segment.find_all("p")
            new_ps = []
            temp_p = ""
            for p_n, p in enumerate(ps):
                if skip_p(p):
                    continue
                elif len(p.text.split()) == 1 and re.compile(u"^.{1,2}[\)|\.]").match(p.text): #make sure it's in form 1. or ש.
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


        new_segments = []
        tables = ["table", "tr"]
        for i, segment in enumerate(segments):
            if isinstance(segment, element.Tag):
                class_ = segment.attrs.get("class", [""])[0]
            else:
                new_segments.append(segment)
                continue
            # if self.significant_class(class_):
            #     new_segments.append(segment)
            #     continue
            if segment.name == "blockquote":  # this is really many children so add them to list
                new_segments += self.get_children_with_content(segment)
            elif segment.name == "table":
                if segment.name == "table":
                    if class_ == "header" or class_ == "RTBorder" or class_ == "RT":
                        new_segments.append(segment)
                        #if class_ != "header":
                        continue
                    elif class_ == "RT_RASHI":
                        new_segments += find_all_p(segment)
                        self.RT_Rashi = True
                        continue
                    elif class_ in ["question", "question2"]:
                        question_in_question = [child for child in segment.descendants if
                                          child.name == "table" and child.attrs["class"][0] in ["question", "question2"]]
                        RT_in_question = [child for child in segment.descendants if
                                          child.name == "table" and child.attrs["class"][0] in ["RT", "RTBorder"]]
                        if RT_in_question:
                            new_segments.append(segment)
                            continue
                            #new_segments += find_all_p(segment)
                        elif question_in_question:
                            new_segments += find_all_p(segment)
                        else:
                            new_segments.append(segment)
                        continue
            else:
                # no significant class and not blockquote or table
                new_segments.append(segment)

        level -= 1
        if level > -1:  # go level deeper unless level isn't > 0
            new_segments = self.check_for_blockquote_and_table(new_segments, level)
        return new_segments

    def unwrap_HTML_tables(self, segments):
        leaves = []
        number = None
        for segment in self.get_children_with_content(segments):
            class_ = "" if isinstance(segment, element.NavigableString) or "class" not in segment.attrs.keys() else segment.attrs["class"][0]
            # go all the way down to the leaves unless we find a signifcant class
            if class_ == "number" and segment.name == "td":
                number = segment.text
            elif segment.name in ["tr"] or (segment.name == "table" and self.significant_class(class_)):
                leaves += self.unwrap_HTML_tables(segment)
            elif segment.name in ["td"] and segment.attrs.get("class", False):
                leaves += self.get_children_with_content(segment)
            else:
                if number:
                    segment.string = number + segment.string
                    number = None
                leaves.append(segment)
        return leaves

    # def unwrap_real_tables(self, segments):
    #     leaves = []
    #     for segment in self.get_children_with_content(segments):
    #         if segment.name in ["table", "tr"]:
    #             class_ = segment.attrs.get("class", [""])[0]
    #             leaves += self.unwrap_real_tables(segment)
    #         elif segment.name in ["td"]:
    #             leaves += segment.contents
    #         else:
    #             raise InputError
    #     return leaves

    def get_children_with_content(self, segment):
        # determine if the text of segment is blank or practically blank (i.e. just a \n or :\n\r) or is just empty space less than 3 chars
        children_w_contents = [el for el in segment.contents if self.relevant_text(el).replace("\n", "").replace("\r", "").replace(": ", "").replace(":", "") != "" and len(self.relevant_text(el)) > 2]
        return children_w_contents


    def check_ref_text_in_sefaria(self, nechama_text, nechama_ref):
        #checks that Nechama's text of nechama_ref is similar to what we have stored for that ref in Sefaria
        sefaria_text, sefaria_ref = self.current_ref_in_sefaria
        assert Ref(nechama_ref)
        #deal with problematic cases first
        if not sefaria_text:
            print "Don't have this text in library."
            print sefaria_ref
            return nechama_ref
        if type(sefaria_text[0]) is list: # it's 2-deep
            print "Found 2-deep"
            return sefaria_ref


        wl = WeightedLevenshtein()
        if "\n" in nechama_text:
            nechama_text = "\n".join(nechama_text.splitlines()[1:]) # get rid of first line because it just says "Rashi:" for example
        if type(sefaria_text) is unicode:
            max_ratio = wl.calculate(nechama_text, sefaria_text)
            found_ref = sefaria_ref
        elif type(sefaria_text) is list:
            found_ref = None
            max_ratio = 0
            for i, line in enumerate(sefaria_text):
                ratio = wl.calculate(nechama_text, line)
                if ratio > max_ratio:
                    max_ratio = ratio
                    found_ref = u"{}:{}".format(sefaria_ref, i+1)
        if max_ratio < 35:
            print "No Match\n" + self.current_url+".html"+": "+nechama_ref
        else:
            return found_ref

    #was part of classify segments
    # table_html = str(segment)
    # # first remove all questions in it which will be columns
    # for td in segment.find_all("td", {"class": "number"}):
    #     td_text = td.text
    #     next_sibling = td.next_sibling
    #     while type(next_sibling) is element.NavigableString and next_sibling == "\n":
    #         next_sibling = next_sibling.next_sibling
    #     next_sibling.string = td.text + next_sibling.text
    #     td.decompose()
    #     table_html = str(segment)

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


    def process_comment_specific_class(self, segments, i, text, segment_class):
        if self.last_comm_index_not_found:
            if type(self.last_comm_index_not_found) is not bool:  # set to True when couldn't find anything but don't even have a_tag
                self.index_not_found_csv.writerow([self.last_comm_index_not_found, text])
            self.last_comm_index_not_found = None
            segments[i] = (segment_class, text, "")
        elif segment_class in self.important_classes:
            quote = self.quotations[-1]
            category, ref = quote
            segments[i] = (segment_class, text, ref)
        else:
            self.add_to_table_classes(segment_class)

    def add_to_table_classes(self, segment_class):
        current_table = self.table_classes.get(segment_class, set())
        our_site = self.year_to_sheet[self.current_en_year]
        her_site = "http://nechama.org.il/pages/" + self.current_url + " in section " + str(self.current_section)
        current_table.add((our_site, her_site))
        self.table_classes[segment_class] = current_table

    def classify_segments(self, segments):
        def set_segment(combined_with_prev_line):
            if (is_perek_pasuk_ref or real_title or found_ref_in_string):
                if not a_tag_is_entire_comment and found_ref_in_string == "" and len(relevant_text.split()) >= 6:
                    combined_with_prev_line = relevant_text
                segments[i] = "reference"
            elif found_a_tag:
                combined_with_prev_line = relevant_text
                segments[i] = "combined but not reference"
                self.index_not_found[u"{}".format(found_a_tag.text)] += 1
                self.last_comm_index_not_found = found_a_tag.text
            else:
                self.last_comm_index_not_found = True
                segments[i] = ("nechama", relevant_text, "")
            return combined_with_prev_line
        """
        Classifies each segments based on its role such as "question", "header", or quote from "bible"
        and then sets each segment to be a tuple that tells us in order:
        who says it, what do they say, where does it link to
        If Nechama makes a comment:
        ("Nechama", text, "")
        If Rashi:
        ("Rashi", text, ref_to_rashi)
        :param segments:
        :return:
        """
        combined_with_prev_line = None
        prev_was_quote = None
        for i, segment in enumerate(segments):
            if isinstance(segment, element.Tag) and segment.name == "table" and segment.attrs["class"][0] in ["question", "question2", "header"]:
                self.process_table(segments, i)
            elif isinstance(segment, element.Tag) and segment.name == "table" and segment.attrs["class"] in [["RT"], ["RTBorder"]]:
                self.add_to_table_classes(segment.attrs["class"][0])
                segments[i] = ("nechama", str(segment), "")
            elif isinstance(segment, element.Tag) and segment.has_attr("class"):
                segment_class = segment.attrs["class"][0]
                if prev_was_quote and prev_was_quote != segment_class and self.RT_Rashi == False:
                    pass
                text = segment.text.replace("\n", "").replace("\r", "")
                if combined_with_prev_line: #i.e.: "Pasuk 5" is the previous line which gets combined with the current line that has Pasuk 5's content
                    text = "<b>" + combined_with_prev_line + "</b><br/><small>" + text + "</small>"
                    combined_with_prev_line = None
                else:
                    text = "<small>" + text + "</small>"
                self.process_comment_specific_class(segments, i, text, segment_class)
                prev_was_quote = segment_class
                continue
            else:
                # if there is no class, then...
                # it is either setting perek/pasuk info
                # or telling us what the next parshan is
                # OR just a comment,
                next_comment_parshan_or_bible = ""
                this_comment_could_be_ref = i < len(segments) - 1 and isinstance(segments[i+1], element.Tag) and isinstance(segments[i], element.Tag)
                if this_comment_could_be_ref:
                    next_comment_parshan_or_bible = "class" in segments[i+1].attrs.keys() and segments[i+1].attrs["class"][0] in self.important_classes
                relevant_text = self.format(self.relevant_text(segment))
                if not next_comment_parshan_or_bible:
                    segments[i] = ('nechama', relevant_text, self.current_parsha_ref[1]) #was self.quotations[0][1]
                else:
                    next_segment_class = segments[i + 1].attrs["class"][0]
                    real_title, found_a_tag, a_tag_is_entire_comment, a_tag_in_long_comment \
                        = self.get_a_tag_from_ref(segment, relevant_text)

                    is_perek_pasuk_ref, real_title, found_ref_in_string \
                        = self.check_ref_and_add_to_quotation_stack(next_segment_class, relevant_text, real_title, a_tag_is_entire_comment)

                    combined_with_prev_line = set_segment(combined_with_prev_line)
                    #set_segment(segments, i, is_perek_pasuk_ref, real_title, found_ref_in_string, relevant_text, a_tag_is_entire_comment, found_a_tag)
                prev_was_quote = ""
        return segments





    def check_ref_and_add_to_quotation_stack(self, next_segment_class, relevant_text, real_title, a_tag_is_entire_comment):
        found_ref_in_string = ""

        # check if it's in Perek X, Pasuk Y format and set perek and pasuk accordingly
        is_torah_ref, new_perek = self.set_current_perek_pasuk(relevant_text, next_segment_class)

        # now add to quotation stack either based on real_title or based on self.current_parsha_ref
        if real_title:  # a ref to a commentator that we have in our system
            if self.current_pasuk:
                self.add_to_quotation_stack(
                    [next_segment_class, u"{} {}:{}".format(real_title, new_perek, self.current_pasuk)])
            else:
                self.add_to_quotation_stack([next_segment_class, u"{} {}".format(real_title, new_perek)])
        elif not real_title and is_torah_ref:  # not a commentator, but instead a ref to the parsha
            self.add_to_quotation_stack(self.current_parsha_ref)
        elif len(relevant_text.split()) < 8:  # not found yet, look it up in library.get_refs_in_string
            print "get refs in string"
            found_ref_in_string = self._get_refs_in_string([relevant_text], next_segment_class,
                                                           add_if_not_found=False)
        return is_torah_ref, real_title, found_ref_in_string

    def get_term(self, poss_title):
        #return the english index name corresponding to poss_title or None
        poss_title = poss_title.strip().replace(":", "")

        # already found it
        if poss_title in self._term_cache:
            return self._term_cache[poss_title]
        # this title is unusual so look in term_mapping for it
        if poss_title in self.term_mapping:
            self._term_cache[poss_title] = self.term_mapping[poss_title]
            return self._term_cache[poss_title]

        term = Term().load({"titles.text": poss_title})
        if poss_title in library.full_title_list('he'):
            self._term_cache[poss_title] = library.get_index(poss_title).title
            return self._term_cache[poss_title]
        elif term:
            term_name = term.name
            likely_index_titles = [u"{} on {}".format(term_name, alt_title) for alt_title in self.current_alt_titles]
            for likely_index_title in likely_index_titles:
                if likely_index_title in library.full_title_list('en'):
                    self._term_cache[poss_title] = likely_index_title
                    return self._term_cache[poss_title]
        self._term_cache[poss_title] = None
        return None


    def add_to_quotation_stack(self, category_and_ref, in_sefaria=True, try_alt_titles=True):
        ref = category_and_ref[1]
        if in_sefaria:
            section_ref = None
            #first see that the Ref exists
            try:
                section_ref = Ref(ref.split(":", 1)[0])
                category_and_ref[1] = Ref(ref)
                #at this point we know we have a real Ref so get text
                sefaria_text = category_and_ref[1].text('he').text
                category_and_ref[1] = category_and_ref[1].normal()
                self.current_ref_in_sefaria = (sefaria_text, category_and_ref[1])
            except InputError as e:
                #try iterating over current_alt_titles and seeing if any allow us to create a Ref that exists so each time we call the function with try_alt_titles of False
                #so that it does not generate an infinite loop
                if section_ref:
                    section_text = category_and_ref[1].replace(":None", "") #hack to only use section, not segments that doesnt exist
                    category_and_ref[1] = section_ref.normal()
                    self.current_ref_in_sefaria = (section_text, category_and_ref[1])
                    self.quotations.append(category_and_ref)
                    self.quotation_stack.append(category_and_ref[1])
                    self.current_pos_in_quotation_stack += 1
                    return category_and_ref
                else:
                    if not try_alt_titles:
                        return False
                    if not hasattr(e, "matched_part"):
                        print e.message
                        return False
                    else: #something was matched and try_alt_titles is True
                        for title in self.current_alt_titles:
                            temp_ref = ref.replace(e.matched_part, "{}, {}".format(e.matched_part, title))
                            category_and_ref[1] = temp_ref
                            found = self.add_to_quotation_stack(category_and_ref, in_sefaria, try_alt_titles=False)
                            if found:
                                break
                        if not found:
                            print e.message
                            self.quotations.append(["parshan", ""])
                            self.quotation_stack.append("")
                            return False
        else:
            print u"{} not found".format(ref)

        self.quotations.append(category_and_ref)
        self.quotation_stack.append(category_and_ref[1])
        self.current_pos_in_quotation_stack += 1
        return category_and_ref[1]

    def remove_from_quotation_stack(self):
        pass

    """ 

    #logic: if it's perek/pasuk, it's clear you add the sefer and perek pasuk info; if the next is bible and there is no perek pasuk,
    #add the entire thing but make sure it's less than a certain number of words AND that part of it is an index in library
    #if it's parshan/midrash/talmud, a tag gets us title (does it get perek and pasuk ever?)
    if not make sure it's less than a certain number of words, take the whole thing AND assert it is an index in library
    """

    def get_a_tag_from_ref(self, segment, relevant_text):
        if segment.name == "a":
            a_tag = segment
        else:
            a_tag = segment.find('a')

        u_tag = segment.find('u')

        # if not a_tag:
        #     a_tag = segment.find("u")

        real_title = ""

        # if a_tag and segment.find("u") and a_tag.text != segment.find("u").text: #case where
        a_tag_is_entire_comment = a_tag_occurs_in_long_comment = False
        if a_tag:
            a_tag_is_entire_comment = len(a_tag.text.split()) == len(segment.text.split())
            a_tag_occurs_in_long_comment = len(segment.text.split()) > 15
            real_title = self.get_term(a_tag.text)
        elif relevant_text in self.term_mapping:
            real_title = self.term_mapping[relevant_text]
        if not real_title and self.RT_Rashi:
            real_title = "Rashi on {}".format(self.current_sefer)
        return (real_title, a_tag, a_tag_is_entire_comment, a_tag_occurs_in_long_comment)



    def _get_refs_in_string(self, strings, next_segment_class, add_if_not_found=True):
        not_found = []
        for string in strings:
            orig = string
            string = "(" + string.replace(u"(", u"").replace(u")", u"") + ")"
            words_to_replace = [u"פרשה", u"*", chr(39), u"פרק", u"פסוק", u"השווה"]
            for word in words_to_replace:
                string = string.replace(u"ל"+word, u"")
                string = string.replace(word, u"")
            string = string.replace(u"  ", u" ")
            string = string.strip()
            refs = library.get_refs_in_string(string)
            if refs:
                self.add_to_quotation_stack([next_segment_class, refs[0].normal()])
                assert len(refs) <= 1 or u"השווה" in orig
                return string[1:-1] #remove ( )
            else:
                not_found.append(orig)
        if len(not_found) == len(strings):
            if add_if_not_found: # nothing found
                #self.add_to_quotation_stack([next_segment_class, strings[-1]], in_sefaria=False)
                self.add_to_quotation_stack(self.current_parsha_ref)
            self.ref_not_found[strings[-1]] += 1
        return ""


    def set_current_perek_pasuk(self, text, next_segment_class):
        text = text.replace(u"פרקים", u"Perek").replace(u"פרק ", u"Perek ").replace(u"פסוקים", u"Pasuk").replace(u"פסוק ", u"Pasuk ").strip()
        digit = re.compile(u"^.{1,2}[\)|\.]").match(text)
        # if next_segment_class == "parshan":e
        #     sefer = u"Parshan on {}".format(self.current_sefer)
        # elif next_segment_class == "bible":
        sefer = self.current_sefer

        if digit:
            text = text.replace(digit.group(0), "").strip()
        text += " " #this is hack so that reg ex works

        perek_comma_pasuk = re.findall("Perek (.{1,5}), (.{1,5})", text)
        perek = re.findall("Perek (.{1,5}\s)", text)
        pasuk = re.findall("Pasuk (.{1,5}(?:-.{1,5})?)", text)
        assert len(perek) in [0, 1]
        assert len(pasuk) in [0, 1]
        assert len(perek_comma_pasuk) in [0, 1]
        if len(perek) == len(pasuk) == len(perek_comma_pasuk) == 0 and ("Pasuk" in text or "Perek" in text):
            pass


        if perek_comma_pasuk:
            perek = perek_comma_pasuk[0][0]
            pasuk = perek_comma_pasuk[0][1]
        else:
            if perek:
                perek = perek[0]
            if pasuk:
                pasuk = pasuk[0]

        #if perek and getGematria(perek) not in self.current_perakim: # We dont want to set the parsha's perek based off Guide for the Perplexed's perek and they are likely not the same
        #    return False                          # so this test should be right almost all the time
        if pasuk:
            if "-" in pasuk: # is a range, correct it
                start = pasuk.split("-")[0]
                end = pasuk.split("-")[1]
                start = getGematria(start)
                end = getGematria(end)
                self.current_pasuk = u"{}-{}".format(start,end)
                text = text.replace(pasuk, "")
            else: # there is a pasuk but is not ranged
                self.current_pasuk = getGematria(pasuk)
                text = text.replace(pasuk, "")

        if perek and text.startswith("Perek"): #second check to prevent things like "Midrash Tadshe Perek Zion" from passing
            text = text.replace(perek, "")
            new_perek = getGematria(perek)
            if new_perek in self.current_perakim:
                self.current_perek = new_perek
            self.current_parsha_ref = [next_segment_class, u"{} {}".format(sefer, new_perek)]
            return True, new_perek
        if pasuk:
            self.current_parsha_ref = [next_segment_class, u"{} {}:{}".format(sefer, self.current_perek, self.current_pasuk)]
            return True, self.current_perek
        return False, self.current_perek




# Check if class is parshan or bible or question or no class
    # If parshan, create tuple with this div's text, name of parshan, and perek pasuk info
    # If bible, create tuple with this div's text, name of sefer, and perek pasuk info
    # If question, create tuple with table's text, "Question", and perek pasuk info
    # If no class, it is telling us who the parshan or perek/pasuk info

    def group_segments(self, tags):
        """
        Currently segments are separated like ["Rashi:", "[Rashi quote here]", "Ramban:", "[Ramban quote here]"...]
        This method goes through and groups them like so ["Rashi: Rashi quote here", "Ramban: Ramban quote here"]
        :param tags: list of BeautifulSoup tags
        :return grouped_segments: list of strings corresponding to each tag's text
        """
        prev_seemed_like_commentary = False
        is_commentary = lambda segment: segment.find(":") in [len(segment) - 1, len(segment) - 2]
        is_pasuk = lambda segment: segment.find(u"פסוק") in [0, 1] and len(segment.strip().split()) == 2
        commentary_header = ""
        grouped_segments = []
        for i, tag in enumerate(tags):
            text = tag.text.replace("\n", "")
            if is_commentary(text) or is_pasuk(text):
                if prev_seemed_like_commentary:
                    print "Two commentary headers in a row in {}.html".format(self.current_url)
                    grouped_segments.append(commentary_header)
                if not text.endswith(":"): #pasuk not commentary
                    text += u":"
                commentary_header = text #store this away to be added to the next segment
            else:
                if commentary_header:
                    text = u"<b>{}</b> {}".format(commentary_header, text)
                    commentary_header = u""
                grouped_segments.append(text)
        return grouped_segments


    def extract_perek_info(self, content):
        perek_info = content.find("p", {"id": "pasuk"}).text
        perek_info = perek_info.replace(u"פרקים", u"Perek").replace(u"פרק", u"Perek").replace(u"פסוקים", u"Pasuk").replace(u"פסוק", u"Pasuk").strip()
        sefer = perek_info.split()[0]
        pereks = re.findall(u"Perek\s+(.{1,3})\s?", perek_info)
        return (sefer, [getGematria(perek) for perek in pereks])


    def download_sheets(self):
        start_after = 19
        for i in range(300):#self.bereshit_parshiot:
            if i <= start_after or str(i) in self.bereshit_parshiot:
                continue
            print "downloading {}".format(i)
            time.sleep(2)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
            response = requests.get("http://www.nechama.org.il/pages/{}.html".format(i), headers=headers)
            if response.status_code == 200:
                with open("{}.html".format(i), 'w') as f:
                    f.write(response.content)
            else:
                print "No page at {}.html".format(i)


    def load_sheets(self):
        page_missing = u'דף שגיאות'
        files = [f for f in os.listdir(".") if f.endswith(".html") and not f.startswith("errors")]
        files = sorted(files, key=lambda x: int(x.replace(".html", "")))
        count = 0
        for which_sheet, i in enumerate(self.bereshit_parshiot):
            i += ".html"
            self.sheet_num = which_sheet + 1
            content = BeautifulSoup(open("{}".format(i)), "lxml")
            header = content.find('div', {'id': 'contentTop'})
            if page_missing in header.text:
                continue
            sheet_title = header.find("h1").text
            hebrew_year = content.find("div", {"id": "year"}).text.replace(u"שנת", u"")
            roman_year = getGematria(hebrew_year) + 1240
            self.current_en_year = roman_year

            parsha = content.find("div", {"id": "paging"}).text
            self.current_parsha = parsha
            self.current_sefer, self.current_perakim = self.extract_perek_info(content)
            self.current_sefer = library.get_index(self.current_sefer)
            self.current_alt_titles = self.current_sefer.nodes.get_titles('en')
            self.current_sefer = self.current_sefer.title
            print "Sheet {}".format(i)
            text = content.find("div", {"id": "contentBody"})
            if parsha not in self.sheets:
                self.sheets[parsha] = {}
            assert roman_year not in self.sheets[parsha].keys()
            self.year_to_url[roman_year] = i
            self.year_to_sheet[roman_year] = sheet_title
            self.current_url = i
            self.current_perek = self.current_perakim[0]
            self.current_pasuk = None
            self.quotations = []
            self.current_pos_in_quotation_stack = 0
            self.quotation_stack = []
            self.current_section = 0
            self.quotation_stack = []
            self.current_parsha_ref = ["bible", u"{} {}".format(self.current_sefer, self.current_perek)]
            self.add_to_quotation_stack(self.current_parsha_ref)
            try:
                self.sheets[parsha][self.current_en_year] = (self.current_url, hebrew_year, self.current_sefer, self.current_perakim, self.parse_as_text(text))
                self.post_text(parsha, self.current_en_year, self.sheets[parsha][self.current_en_year])
            # except AssertionError:
            #     print "ASSERTION ERROR WITH {}".format(i)
            except InputError:
                print "INPUT ERROR WITH {}".format(i)

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

        text = text.replace("\n", " ") #just getting rid of excessive line breaks
        while "  " in text:
            text = text.replace("  ", " ")

        # now get the tags back and remove nonsense chars
        text = text.replace("$!u$", "<u>").replace("$/!u$", "</u>")
        text = text.replace("$!b$", "<b>").replace("$/!b$", "</b>")

        return (found_difficult + text).strip()


    def fix_ref(self, ref, comment):
        #first remove HTML from comment
        comment = bleach.clean(comment, strip=True)
        ref_obj = Ref(ref)

        #if it has no text, generates error, so get its section level ref that has text
        text = ref_obj.text('he').text
        while not text:
            print "looking for text..."
            self.refs_to_nowhere[ref] = "Section {}: http://nechama.org.il/pages/".format(self.current_section)+self.current_url
            if ref_obj.is_segment_level():
                ref_obj = ref_obj.section_ref()
            elif ref_obj.is_section_level():
                ref_obj = ref_obj.top_section_ref()
            text = ref_obj.text('he').text

        #try to get segment level from section
        new_ref = refine_ref_by_text(ref_obj, "", comment)  # can be None, same ref as str or Ref
        if new_ref is None:
            self.doesnt_match[ref] = comment
        elif new_ref == True:
            self.good_match += 1
        else:
            orig_ref = ref
            ref = new_ref if isinstance(new_ref, str) else new_ref.normal()
            if orig_ref == ref:
                self.good_match += 1
            else:
                self.fixed_match += 1

        #if it is still a top section level set it as a range
        if Ref(ref).top_section_ref() == Ref(ref):
            ref = Ref(ref).as_ranged_segment_ref().normal()

        #if still no text, set to ""
        if not Ref(ref).text('he').text:
            return ""
        return ref

    def get_text_links_and_sources(self, text_list, parsha, year):
        """
        :param text_list:
        :param parsha:
        :param year:
        :return:
        """
        links = []
        sources = []
        links_set = set() #because there will be many duplicates

        #now that we have the correct size of the lists, we can generate the ranged_ref nechama_ref
        term = Term().load({"titles.text": parsha})
        assert term, u"{} doesn't have term".format(parsha)
        nechama_ref = u"{}, {} {}".format(self.en_title_project, term.name, year)

        # remove non-tuples from list since they are useless
        for i, section in enumerate(text_list):
            section = [el for el in text_list[i] if isinstance(el, tuple)]
            nechama_sec_range_ref = u"{}:{}:1-{}".format(nechama_ref, i+1, len(section))
            for j, segment in enumerate(section):
                type, comment, ref = segment
                if ref:
                    ref = self.fix_ref(ref, comment)
                comment = self.remove_hyper_links(comment)
                if type == "nechama":
                    source = {"outsideText": comment}
                elif not ref:
                    source = {"outsideText": comment,
                              "options": {
                                  "indented": "indented-1",
                                  "sourceLayout": "",
                                  "sourceLanguage": "hebrew",
                                  "sourceLangLayout": ""
                              }
                            }
                elif ref and type in self.important_classes:
                    if isinstance(ref, Ref):
                        heRef = ref.he_normal()
                    else:
                        heRef = Ref(ref).he_normal()
                    source = {"ref": ref, "heRef": heRef,
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
                    link = {"refs": [nechama_sec_range_ref,
                                     ref],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "nechama_linker"
                            }
                    links_set.add(str(link))
                else:
                    raise InputError
                sources.append(source)
                section[j] = comment
            text_list[i] = section



        links = list(links_set)
        links = [eval(el) for el in links]
        return text_list, links, sources


    def create_index(self):
        root = SchemaNode()
        root.add_primary_titles(self.en_title_project, self.he_title_project)
        for parsha, sheets_by_year in self.sheets.items():
            parsha_node = JaggedArrayNode()
            term = Term().load({"titles.text": parsha})
            assert term, u"{} doesn't have term".format(parsha)
            assert len(term.get_titles('he')[0].split()) == 1
            parsha_node.add_primary_titles(term.name, term.get_titles('he')[0])
            parsha_node.add_structure(["Year", "Section", "Paragraph"])
            parsha_node.addressTypes = ["Year", "Integer", "Integer"]
            parsha_node.validate()
            root.append(parsha_node)
        index = {
            "title": self.en_title_project,
            "schema": root.serialize(),
            "categories": ["Tanakh", "Commentary"],
            "dependence": "Commentary"
        }
        post_index(index, server=self.server)


    def post_text(self, parsha, en_year, sheet):
        #self.create_index()
        nechama_text = {}
        nechama_sheet = {}
        all_links = []
        important_classes = ["parshan", "midrash", "talmud", "bible", "commentary"]
        term = Term().load({"titles.text": parsha})
        assert term, u"{} doesn't have term".format(parsha)
        parsha = term.name
        nechama_text[parsha] = {}
        nechama_sheet[parsha] = {}
        url, he_year, sefer, perakim, text_tuples = sheet
        sheet_title = self.year_to_sheet[en_year]
        he_year_num = getGematria(he_year)
        text, links, sources = self.get_text_links_and_sources(text_tuples, parsha, en_year)
        self.links += links
        nechama_text[parsha][he_year_num] = text
        self.prepare_sheet(u"{}: {}".format(self.current_parsha, sheet_title), (en_year, he_year), sources)
        # nechama_text[parsha] = convertDictToArray(nechama_text[parsha])
        # send_text = {
        #     "text": nechama_text[parsha],
        #     "language": "he",
        #     "versionTitle": self.versionTitle,
        #     "versionSource": self.versionSource
        # }
        #post_text(u"{}, {}".format(self.en_title_project, parsha), send_text, server=self.server)
    #post_link(self.links, server=self.server)
        # for year, sheet in enumerate(nechama_text[parsha]):
        #     if year < 1941:
        #         continue
        #     for section_n, section in enumerate(sheet):
        #         post_text(u"{}, {} {}:{}".format(self.en_title_project, parsha, year+1, section_n+1), section, server=self.server)

    def prepare_sheet(self, title, years, sources):
       print title
       en_year, he_year = years
       sheet_json = {}
       sheet_json["status"] = "public"
       sheet_json["title"] = title
       sheet_json["summary"] = u"{} ({})".format(en_year, he_year)
       sheet_json["sources"] = sources
       # sheet_json["dateC  eated"] = 2012
       sheet_json["options"] = {"numbered": 0,"assignable": 0,"layout": "sideBySide","boxed": 0,"language": "hebrew","divineNames": "noSub","collaboration": "none", "highlightMode": 0, "bsd": 0,"langLayout": "heRight"}
       #post_sheet(sheet_json, server=self.server)

"""
from research.source_sheet_disambiguator.main import refine_ref_by_text
en = ""  #  let's assume no English in Nechama
he = u"some hebrew text"  # hebrew text associated with a ref in a Nechama source sheet
ref = Ref("Genesis 1:1")
new_ref = refine_ref_by_text(ref, en, he)
if new_ref is not None:
    print "refined the ref!"
else:
    print "ref was fine"
# """
#
# def fix_refs_in_source_sheets():
#     sheets = db.sheets().find({"owner": 15399}) # get all of my source sheets, which are Nechama Leibowitz
#     for sheet in sheets:
#         for source in sheet["sources"]:
#             if getattr(source, "ref", None):  # this has a ref...
#                 ref = source["ref"]
#                 old_ref = ref
#                 text = source["text"]["he"]
#                 found_ref = refine_ref_by_text(ref, "", text)



if __name__ == "__main__":
    sheets = Sheets()
    #sheets.download_sheets()
    sheets.load_sheets()
    f = open("tables.csv", 'w')
    writer = UnicodeWriter(f)
    rows = []
    print "Doesnt match, Good Match, Fixed Match"
    print len(sheets.doesnt_match)
    print sheets.good_match
    print sheets.fixed_match
    for ref, site in sheets.refs_to_nowhere.items():
        rows.append([ref, site])
    rows = sorted(rows, key=lambda x: x[0].split()[0])
    writer.writerows(rows)


    # create table csv
    # for type, site_set in sheets.table_classes.items():
    #     for site in site_set:
    #         he_title, nechama_site = site
    #         rows.append([type, he_title, nechama_site])
    #
    # rows = sorted(rows, key=lambda x: x[0])
    # writer.writerows(rows)
    #
    # f.close()
    #

    # indexes not found
    # for index in set(sheets.index_not_found):
    #     print index
    # pass
