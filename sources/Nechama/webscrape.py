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
from research.link_disambiguator.main import *
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
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
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
        self.current_pasukim = []
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
        self.index_not_found = {} #indexes not found in library
        self.intro_to_many_comment_finds = Counter() #2.html 5th section Shadal
        self.significant_class = lambda class_: True#"question" in class_ #class_ in ["header", "question"] or "question" in class_
        self.RT_Rashi = False
        self.term_mapping = {
            u"מורה נבוכים א'": u"Guide for the Perplexed, Part 1",
            u"מורה נבוכים ב'": u"Guide for the Perplexed, Part 2",
            u"מורה נבוכים ג'": u"Guide for the Perplexed, Part 3",
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
        self.orig_good_count = 0
        self.orig_bad_count = 0


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
            elif len(p.text.split()) == 1 and re.compile(u"^.{1,2}[\)|\.]").match(
                    p.text):  # make sure it's in form 1. or ש.
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

#logic is if it's a header don't even count it; if it's not question or header, count it; if it's a question with tables below it, don't count it

    def check_for_blockquote_and_table(self, segments, level=2):
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


    def get_children_with_content(self, segment):
        # determine if the text of segment is blank or practically blank (i.e. just a \n or :\n\r) or is just empty space less than 3 chars
        children_w_contents = [el for el in segment.contents if self.relevant_text(el).replace("\n", "").replace("\r", "").replace(": ", "").replace(":", "") != "" and len(self.relevant_text(el)) > 2]
        return children_w_contents

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
            formatted_text = self.format(table_html)
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

    def add_to_table_classes(self, segment_class):
        current_table = self.table_classes.get(segment_class, set())
        our_site = self.year_to_sheet[self.current_en_year]
        her_site = "http://nechama.org.il/pages/" + self.current_url + " in section " + str(self.current_section)
        current_table.add((our_site, her_site))
        self.table_classes[segment_class] = current_table

    def classify_segments(self, segments):
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
        def set_ref_segment(combined_with_prev_line):
            #when she is quoting a reference to a text, this function sets segments[i]
            if (is_perek_pasuk_ref or real_title or found_ref_in_string):
                if not a_tag_is_entire_comment and found_ref_in_string == "" and len(relevant_text.split()) >= 6:
                    #edge case where you found the ref but Nechama said something else in addition to the ref
                    #so we want to keep the text
                    combined_with_prev_line = relevant_text
                    #could be Comment.about = relevant_text; Comment.ref = ref; Comment.ref_in_library = True;

                segments[i] = "reference"
            elif found_a_tag:
                #found no reference but did find an a_tag so this is a ref so keep the text
                combined_with_prev_line = relevant_text
                #could be Comment.ref = relevant_text; Comment.about = ""; Comment.ref_in_library = False;
                segments[i] = "combined but not reference"
                self.last_comm_index_not_found = found_a_tag.text
            else:
                self.last_comm_index_not_found = True
                segments[i] = ("nechama", relevant_text, "")
            return combined_with_prev_line

        combined_with_prev_line = None
        prev_was_quote = None
        for i, segment in enumerate(segments):
            # sanity check:
            # determine if it's worth looking to see what this ref is:
            # if it's the last one, it's not a ref because a comment needs to come after it
            # if the next one isn't a Tag, this can't be a ref because comments are always Tags with classes
            # indicating parshan, bible, etc.
            # also make sure the next one has a class in self.important_classes
            # if it doesn't meet all the criteria, then it's just a comment by Nechama
            relevant_text = self.format(self.relevant_text(segment))  # if it's Tag, tag.text; if it's NavigableString, just the string
            next_comment_parshan_or_bible = ""
            this_comment_could_be_ref = i < len(segments) - 1 and isinstance(segments[i + 1], element.Tag) and isinstance(segments[i], element.Tag)
            if this_comment_could_be_ref:
                next_comment_parshan_or_bible = "class" in segments[i + 1].attrs.keys() and \
                                                segments[i + 1].attrs["class"][0] in self.important_classes

            if isinstance(segment, element.Tag) and segment.name == "table":
                if segment.attrs["class"][0] in ["question", "question2", "header"]:
                    self.process_table(segments, i)
                elif segment.attrs["class"] in [["RT"], ["RTBorder"]]:  #these tables we want as they are so just str(segment)
                    self.add_to_table_classes(segment.attrs["class"][0])
                    segments[i] = ("nechama", str(segment), "")
            elif isinstance(segment, element.Tag) and segment.has_attr("class"):
                #this is a comment by a commentary, bible, or midrash
                segment_class = segment.attrs["class"][0] #is it parshan, bible, or midrash?
                assert len(segment.attrs["class"]) == 1, "More than one class"
                # if prev_was_quote and prev_was_quote != segment_class and self.RT_Rashi == False:
                #     pass
                orig_text = segment.text.replace("\n", "").replace("\r", "")
                if combined_with_prev_line: #i.e.: "Pasuk 5" is the previous line which gets combined with the current line that has Pasuk 5's content
                    formatted_text = "<b><small>" + combined_with_prev_line + "</b><br/>" + orig_text + "</small>"
                    combined_with_prev_line = None
                else:
                    formatted_text = "<small>" + orig_text + "</small>"
                self.process_comment_specific_class(segments, i, formatted_text, orig_text, segment_class)
                #prev_was_quote = segment_class
                continue
            elif not next_comment_parshan_or_bible or not this_comment_could_be_ref:  # above criteria not met, just an ordinary comment
                segments[i] = ('nechama', relevant_text, "")
            else: #must be a Comment
                next_segment_class = segments[i + 1].attrs["class"][0] #get the class of this ref and it's comment
                real_title, found_a_tag, a_tag_is_entire_comment, a_tag_in_long_comment \
                    = self.get_a_tag_from_ref(segment, relevant_text)

                is_perek_pasuk_ref, real_title, found_ref_in_string \
                    = self.check_ref_and_add_to_quotation_stack(next_segment_class, relevant_text, real_title)

                combined_with_prev_line = set_ref_segment(combined_with_prev_line)
                prev_was_quote = ""
        return segments


    def check_ref_and_add_to_quotation_stack(self, next_segment_class, relevant_text, real_title):
        found_ref_in_string = ""

        # check if it's in Perek X, Pasuk Y format and set perek and pasuk accordingly
        is_tanakh = (relevant_text.startswith(u"פרק ") or relevant_text.startswith(u"פסוק ") or
                     relevant_text.startswith(u"פרקים ") or relevant_text.startswith(u"פסוקים "))
        is_perek_pasuk_ref, new_perek, new_pasuk = self.set_current_perek_pasuk(relevant_text, next_segment_class, is_tanakh)

        # now add to quotation stack either based on real_title or based on self.current_parsha_ref
        if real_title:  # a ref to a commentator that we have in our system
            if new_pasuk:
                added_ref = self.add_to_quotation_stack([next_segment_class, u"{} {}:{}".format(real_title, new_perek, new_pasuk)])
            else:
                added_ref = self.add_to_quotation_stack([next_segment_class, u"{} {}".format(real_title, new_perek)])
            if not added_ref:
                self.quotations.append([next_segment_class, ""])
                self.quotation_stack.append("")
        elif not real_title and is_tanakh:  # not a commentator, but instead a ref to the parsha
            self.add_to_quotation_stack(["bible", "{} {}:{}".format(self.current_sefer, new_perek, new_pasuk)])
        elif len(relevant_text.split()) < 8:  # not found yet, look it up in library.get_refs_in_string
            found_ref_in_string = self._get_refs_in_string([relevant_text], next_segment_class, add_if_not_found=False)
            if not found_ref_in_string:
                self.quotations.append([next_segment_class, ""])
                self.quotation_stack.append("")
        return is_perek_pasuk_ref, real_title, found_ref_in_string

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
                            return False
        else:
            print u"{} not found".format(ref)

        self.quotations.append(category_and_ref)
        self.quotation_stack.append(category_and_ref[1])
        self.current_pos_in_quotation_stack += 1
        return category_and_ref[1]

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
        if not real_title and self.RT_Rashi: #every ref in RT_Rashi is really to Rashi
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


    def pasuk_in_parsha_pasukim(self, new_pasuk, perakim=None):
        if perakim is None:
            perakim = self.current_perakim
        for perek in perakim:
            possible_ref = Ref("Genesis " + perek + ":" + new_pasuk)
            if self.current_pasukim.contains(possible_ref):
                return possible_ref
        return None


    def set_current_parsha_ref(self, is_tanakh, sefer):
        pass


    def set_current_perek(self, perek, is_tanakh, sefer):
        new_perek = str(getGematria(perek))
        if is_tanakh:
            if new_perek in self.current_perakim:
                self.current_perek = str(new_perek)
                self.current_parsha_ref = ["bible", u"{} {}".format(sefer, new_perek)]
            else:
                print
        return True, new_perek, None


    def set_current_pasuk(self, pasuk, is_tanakh):
        if "-" in pasuk:  # is a range, correct it
            start = pasuk.split("-")[0]
            end = pasuk.split("-")[1]
            start = getGematria(start)
            end = getGematria(end)
            new_pasuk = u"{}-{}".format(start, end)
        else:  # there is a pasuk but is not ranged
            new_pasuk = str(getGematria(pasuk))

        if is_tanakh:
            poss_ref = self.pasuk_in_parsha_pasukim(new_pasuk)
            if poss_ref:
                self.current_perek = poss_ref.sections[0]
                self.current_pasuk = poss_ref.sections[1]
            else:
                print
                self.current_parsha_ref = ["bible", u"{} {}".format(self.current_sefer, self.current_perek)]
        return True, self.current_perek, new_pasuk


    def set_current_perek_pasuk(self, text, next_segment_class, is_tanakh=True):
        text = text.replace(u"פרקים", u"Perek").replace(u"פרק ", u"Perek ").replace(u"פסוקים", u"Pasuk").replace(u"פסוק ", u"Pasuk ").strip()
        digit = re.compile(u"^.{1,2}[\)|\.]").match(text)
        # if next_segment_class == "parshan":
        #     sefer = u"Parshan on {}".format(self.current_sefer)
        # elif next_segment_class == "bible":
        sefer = self.current_sefer

        if digit:
            text = text.replace(digit.group(0), "").strip()
        text += " " #this is hack so that reg ex works

        perek_comma_pasuk = re.findall("Perek (.{1,5}), (.{1,5})", text)
        if not perek_comma_pasuk:
            perek_comma_pasuk = re.findall("Perek (.{1,5}),? Pasuk (.{1,5})", text)
        perek = re.findall("Perek (.{1,5}\s)", text)
        pasuk = re.findall("Pasuk (.{1,5}(?:-.{1,5})?)", text)
        assert len(perek) in [0, 1]
        assert len(pasuk) in [0, 1]
        assert len(perek_comma_pasuk) in [0, 1]
        if len(perek) == len(pasuk) == len(perek_comma_pasuk) == 0 and ("Pasuk" in text or "Perek" in text):
            pass

        if not perek_comma_pasuk:
            if perek:
                perek = perek[0]
                return self.set_current_perek(perek, is_tanakh, sefer)
            if pasuk:
                pasuk = pasuk[0]
                return self.set_current_pasuk(pasuk, is_tanakh)
        else:
            perek = perek_comma_pasuk[0][0]
            pasuk = perek_comma_pasuk[0][1]
            new_perek = str(getGematria(perek))
            if "-" in pasuk:  # is a range, correct it
                start = pasuk.split("-")[0]
                end = pasuk.split("-")[1]
                start = getGematria(start)
                end = getGematria(end)
                new_pasuk = u"{}-{}".format(start, end)
            else:  # there is a pasuk but is not ranged
                new_pasuk = str(getGematria(pasuk))

            if is_tanakh:
                poss_ref = self.pasuk_in_parsha_pasukim(new_pasuk, perakim=[new_perek])
                if poss_ref:
                    self.current_perek = poss_ref.sections[0]
                    self.current_pasuk = poss_ref.sections[1]
                    assert str(poss_ref.sections[0]) == new_perek
                    assert str(poss_ref.sections[1]) == new_pasuk
                    self.current_parsha_ref = ["bible", u"{} {}".format(self.current_sefer, self.current_perek)]
                else:
                    print
            return True, new_perek, new_pasuk
        return False, self.current_perek, self.current_pasuk




# Check if class is parshan or bible or question or no class
    # If parshan, create tuple with this div's text, name of parshan, and perek pasuk info
    # If bible, create tuple with this div's text, name of sefer, and perek pasuk info
    # If question, create tuple with table's text, "Question", and perek pasuk info
    # If no class, it is telling us who the parshan or perek/pasuk info

    def extract_perek_info(self, content):
        def get_pasukim_for_perek(sefer, perek):
            en_sefer = library.get_index(sefer).title
            return str(len(Ref(u"{} {}".format(en_sefer, perek)).all_segment_refs()))
        #three formats: Perek 2; Perek 2, Pasuk 3-9; Perek 2, 4 - Perek 3, 2 (last one may lose pasuk info as well)
        perek_info = content.find("p", {"id": "pasuk"}).text
        print perek_info
        sefer = perek_info.split()[0]
        en_sefer = library.get_index(sefer).title
        perek_info = perek_info.replace(u"פרקים", u"Perek").replace(u"פרק", u"Perek").replace(u"פסוקים", u"Pasuk").replace(u"פסוק", u"Pasuk").strip()
        perek_info = " ".join(perek_info.split()[1:])
        if len(perek_info.split("Perek")) - 1 == 2: #we know it's the third case
            pereks = [perek_info.split(" - ")[0], perek_info.split(" - ")[1]]
            pasuks = [-1, -1]
            for p, perek in enumerate(pereks):
                if ", " in perek:
                    pereks[p] = str(getGematria(perek.replace("Perek ", "").split(", ")[0]))
                    pasuks[p] = pereks[p] + ":" + str(getGematria(perek.replace("Perek ", "").split(", ")[1]))
                else:
                    pereks[p] = str(getGematria(pereks[p].replace("Perek ", "")))
            if pasuks[0] == -1:
                pasuks[0] = pereks[0] + ":1"
            if pasuks[1] == -1:
                pasuks[1] = pereks[1] + ":" + get_pasukim_for_perek(sefer, pereks[1])
            pasuks = Ref("{} {}-{}".format(en_sefer, pasuks[0], pasuks[1]))
        elif "Pasuk" in perek_info: #we know it's the second case
            pereks = re.findall(u"Perek\s+(.{1,3})\s?", perek_info)
            assert len(pereks) is 1
            pereks = [str(getGematria(pereks[0]))]
            pasuks = re.findall(u"Pasuk\s+(.{1,8})\s?", perek_info)[0].split(" - ")
            assert len(pasuks) is 2
            for p, pasuk in enumerate(pasuks):
                pasuks[p] = getGematria(pasuk)
            pasuks = range(pasuks[0], pasuks[1]+1)
            pasuks = Ref(en_sefer+" "+pereks[0]+":"+str(pasuks[0])+"-"+str(pasuks[-1]))
            #pasuks.insert("multiple perakim", 0)
        else: #first case
            pereks = re.findall(u"Perek\s+(.{1,3})\s?", perek_info)
            assert len(pereks) is 1
            pereks = [str(getGematria(pereks[0]))]
            pasuks = []
            last_pasuk = get_pasukim_for_perek(sefer, pereks[0])
            pasuks = Ref(en_sefer+" "+pereks[0]+":1-"+last_pasuk)

        #pasuks = re.findall(u"Pasuk\s+(.{1,8})\s?", perek_info)[0].split(" - ")
        #pasuks = [getGematria(pasuk) for pasuk in pasuks]
        #pasuks = pasuks[0] if len(pasuks) == 1 else range(pasuks[0], pasuks[1])
        print pereks
        print pasuks
        return (sefer, pereks, pasuks)


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

    def load_sheet(self, which_sheet, i):
        i += ".html"
        page_missing = u'דף שגיאות'
        self.sheet_num = which_sheet + 1
        content = BeautifulSoup(open("./html_sheets/{}".format(i)), "lxml")
        header = content.find('div', {'id': 'contentTop'})
        if page_missing in header.text:
            return
        sheet_title = header.find("h1").text
        hebrew_year = content.find("div", {"id": "year"}).text.replace(u"שנת", u"")
        roman_year = getGematria(hebrew_year) + 1240
        self.current_en_year = roman_year

        parsha = content.find("div", {"id": "paging"}).text
        self.current_parsha = parsha
        print i
        self.current_sefer, self.current_perakim, self.current_pasukim = self.extract_perek_info(content)
        self.current_sefer = library.get_index(self.current_sefer)
        self.current_alt_titles = self.current_sefer.nodes.get_titles('en')
        self.current_sefer = self.current_sefer.title
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
        self.sheets[parsha][self.current_en_year] = (
        self.current_url, hebrew_year, self.current_sefer, self.current_perakim, self.parse_as_text(text))
        self.post_text(parsha, self.current_en_year, self.sheets[parsha][self.current_en_year])

    def load_sheets(self):
        files = [f for f in os.listdir("./html_sheets/") if f.endswith(".html") and not f.startswith("errors")]
        files = sorted(files, key=lambda x: int(x.replace(".html", "")))
        count = 0
        for which_sheet, i in enumerate(self.bereshit_parshiot):
            self.load_sheet(which_sheet, i)


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


    def fix_ref(self, ref, comment):

        # ld = Link_Disambiguator()
        # main_tc = TextChunk(Ref("Tosafot on Eruvin 92a:1:1"), "he")
        # other_tc = TextChunk(Ref(ref), "he")
        # print ld.disambiguate_segment((comment, "Nechama"), [other_tc])
        #
        # tokenize_words = lambda str: [s for s in str.split(" ") if s]
        # matcher = ParallelMatcher(tokenize_words, max_words_between=1, min_words_in_match=3, ngram_size=4,
        #                           parallelize=False, calculate_score=None, all_to_all=False,
        #                           verbose=False)
        # tc = TextChunk(Ref(ref), lang='he')
        # match_list = matcher.match(tc_list=[(comment, "Nechama"), tc], return_obj=True)
        # match_list = matcher.match(tc_list=[(comment, "Nechama"), (tc.text, "Base"), tc], return_obj=True)



        #first remove HTML from comment
        ref_obj = Ref(ref)

        #if it has no text, generates error, so get its section level ref that has text
        text = ref_obj.text('he').text
        if not text:
            return ""
        orig_didnt_find_text = False


        #try to get segment level from section
        try:
            comment = re.sub(u'\u05d3"\u05d4:? .+?:', u"", comment)
            new_ref = refine_ref_by_text(ref_obj, "", comment, 20, alwaysCheck=True, truncateSheet=False, daf_skips=2, rashi_skips=2, overall=2)  # can be None, same ref as str or Ref
        except InputError as e:
            new_ref = None

        if new_ref is None:
            if ref.startswith("Genesis"):
                return ""
            else:
                self.doesnt_match[ref_obj.normal()] = comment
                return ref_obj.normal()
        elif new_ref == True:
            self.good_match += 1
        else:
            orig_ref = ref
            ref = new_ref if isinstance(new_ref, str) else new_ref.normal()
            if orig_ref == ref: #compares them as strings
                self.good_match += 1
            else:
                self.fixed_match += 1
                ref_obj = Ref(ref)

        #if it is still a top section level set it as a range
        # if Ref(ref).top_section_ref() == Ref(ref):
        #     ref_obj = Ref(ref).as_ranged_segment_ref()

        #if still no text, set to ""
        if not ref_obj.text('he').text:
            return ref_obj.normal()
        return ref_obj

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
                formatted_comment = ""
                if len(segment) == 3:
                    type, comment, ref = segment
                elif len(segment) == 4:
                    type, comment, formatted_comment, ref = segment #difference between them is second one is formatted
                if ref:
                    orig_ref = ref
                    ref = self.fix_ref(ref, comment)
                    if not ref:
                        comment = "<b>"+Ref(orig_ref).he_normal()+"</b><br/>"+comment
                comment = formatted_comment if formatted_comment else comment
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
                elif ref and not isinstance(ref, Ref): #this happens when we pick up a reference that we can't be sure is accurate
                    heRef = Ref(ref).he_normal()
                    comment = "<small><b>" + heRef + "</b></small><br/>" + comment
                    source = {"outsideText": comment,
                              "options": {
                                  "indented": "indented-1",
                                  "sourceLayout": "",
                                  "sourceLanguage": "hebrew",
                                  "sourceLangLayout": ""
                              }
                              }
                elif ref and type in self.important_classes:
                    heRef = ref.he_normal()
                    ref = ref.normal()
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
       post_sheet(sheet_json, server=self.server)


"""
Ideas:
Revisit ref.startswith(“Genesis”) returning “”

30.html section 4 
"""
if __name__ == "__main__":
    sheets = Sheets()
    #sheets.download_sheets()
    sheets.load_sheets()
    f = open("tables.csv", 'w')
    writer = UnicodeWriter(f)
    rows = []
    print "Doesnt match, Unchanged Match, More specific Match"
    print len(sheets.doesnt_match)
    print sheets.good_match
    print sheets.fixed_match
    print "original text was not found:"
    print sheets.orig_good_count
    print sheets.orig_bad_count
    for ref, text in sheets.doesnt_match.items():
        site_text = Ref(ref).text('he').text
        if not site_text:
            print "Found problem with ref {}".format(ref)
        if isinstance(site_text, list):
            if len(site_text) > 0 and isinstance(site_text[0], list):
                print "Found 2-d list with ref {}".format(ref)
            else:
                site_text = "\n".join(site_text)
                rows.append([ref, text, site_text])
        else:
            rows.append([ref, text, site_text])
    rows = sorted(rows, key=lambda x: x[0].split()[0])
    writer.writerow(["Nechama Ref", "Nechama Text", "Sefaria Text"])
    writer.writerows(rows)

    i = open("index_not_found.csv", 'w')
    writer = UnicodeWriter(i)
    writer.writerow(["Index", "Ref", "Text"])
    for index, ref_texts in sheets.index_not_found.items():
        for ref_text in ref_texts:
            ref, text = ref_text
            writer.writerow([index, ref[1], text])

    i.close()


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

