#encoding=utf-8
import requests
import re
from bs4 import BeautifulSoup, element
from sources.functions import getGematria
import logging
logger = logging.getLogger(__name__)
import django
django.setup()
from sefaria.model import *
from collections import Counter
import time
from sefaria.system.exceptions import *
class Sheets:
    def __init__(self):
        self.parsha_and_year_to_url = {}
        self.bereshit_parshiot = ["1", "2", "30", "62", "84", "148","212","274","302","378","451","488","527","563","570","581","750","787","820","844","894","929","1021","1034","1125","1183","1229","1291","1351","1420"]
        self.sheets = {}
        self.current_url = ""
        self.current_perek = 1
        self.current_perakim = []
        self.current_pasuk = None
        self.current_sefer = ""
        self.quotation_stack = [] # keeps track of layers of quotations Nechama makes
        self.found = set() #found holds all titles of books we found in the library
        self.index_not_found = Counter() #indexes not found in library
        self.intro_to_many_comment_finds = Counter() #2.html 5th section Shadal
        self.significant_class = lambda class_: class_ in ["header", "parshan", "question"] or "question" in class_



    def parse_as_sheets(self, text):
        pass


    def parse_as_text(self, text):
        sections = 0
        sheet_sections = []
        for div in text.find_all("div"):
            if "ContentSection" in div['id']: #sections within source sheets
                sections += 1
                assert str(sections) in div['id']

                # removes nodes with no content
                segments = self.get_children_with_content(div)

                # blockquote is really just its children so get replace it with them
                # and tables need to be handled recursively
                segments = self.check_for_blockquote_and_table(segments)

                # here is the main logic of parsing
                segments = self.classify_segments(segments)

                sheet_sections.append(segments)
        return sheet_sections


    def check_for_blockquote_and_table(self, segments):
        new_segments = []
        for i, segment in enumerate(segments):
            if isinstance(segment, element.Tag):
                class_ = segment.attrs.get("class", [""])[0]
            if self.significant_class(class_):
                new_segments.append(segment)
                continue
            if segment.name == "blockquote": #this is really many children so add them to list
                extra_segments = self.get_children_with_content(segment)
                new_segments += extra_segments
            elif segment.name in ["table", "tr", "td"]:
                extra_segments = self.unwrap_tables(segment)
                new_segments += extra_segments
            else:
                #no significant class and not blockquote or table
                new_segments.append(segment)
        return new_segments

    def unwrap_tables(self, segments):
        leaves = []
        for segment in self.get_children_with_content(segments):
            class_ = "" if isinstance(segment, element.NavigableString) or segment.attrs == {} else segment.attrs["class"][0]
            # go all the way down to the leaves unless we find a signifcant class
            if segment.name in ["table", "td", "tr"] and not self.significant_class(class_):
                leaves += self.unwrap_tables(segment)
            else:
                leaves.append(segment)
        return leaves

    def get_children_with_content(self, segment):
        # determine if the text of segment is blank or practically blank (i.e. just a \n or :\n\r) or is just empty space less than 3 chars
        relevant_text = lambda segment: segment if isinstance(segment, element.NavigableString) else segment.text
        children_w_contents = [el for el in segment.contents if relevant_text(el).replace("\n", "").replace("\r", "").replace(": ", "").replace(":", "") != ""]
        children_w_contents = [el for el in children_w_contents if len(relevant_text(el)) > 2]
        return children_w_contents

    def classify_segments(self, segments):
        """
        Classifies each segments based on its role such as "question", "header", or quote from "bible"
        and then sets each segment to be a tuple that tells us in order:
        who says it, what do they say, where does it link to
        If Nechama makes a comment:
        ("Nechama", text, current_sefer, current_perek, current_pasuk)
        If Rashi makes a comment:
        ("Rashi", text, current_sefer, current_perek, current_pasuk) UNLESS she specified on the line before a specific
        perek and pasuk for Rashi
        Likewise, a bible quotation:
        ("Bible", text, current_sefer, current_perek, current_pasuk)
        :param segments:
        :return:
        """
        for i, segment in enumerate(segments):
            if segment.has_attr("class"):
                segment_class = segment.attrs["class"][0]
                text = segment.text.replace("\n", "").replace("\r", "")
                if segment_class == "header" or "question" in segment_class:
                    segments[i] = ("nechama", text, self.quotation_stack[0])
                    assert (i == 0) ^ (segment_class != "header"), "Header should be first element."
                elif segment_class == "bible":
                    segments[i] = ("bible", text, self.quotation_stack.pop())
                elif segment_class in ["parshan", "midrash", "talmud"]:
                    # need to put check in here about unlinked_parshan_others and use it instead of self.current_*
                    segments[i] = ("commentary", text, self.quotation_stack.pop())
                else:
                    # must be either header, parshan, bible, or question
                    raise InputError, segment.text
            else:
                # it is setting perek/pasuk info or telling us what the next parshan is, check next segment to know whether this is setting pasuk or parshan
                assert segments[i+1], "Assumed that this cannot be the last in the section/sheet, but it is."
                if "class" in segments[i+1].attrs.keys():
                    #first set what this line is... either something that should be combined with next line like "Rashi"
                    #or it is legitimately a comment of its own;
                    if len(segment.text.split()) > 10:
                        segments[i] = ('nechama', segment.text, self.quotation_stack[0])
                    else:
                        segments[i] = ("combined_with_next_line", segment.text, "")

                    next_segment_class = segments[i+1].attrs["class"][0]
                    if next_segment_class == "bible":
                        self.set_current_perek_pasuk(segment.text)
                    elif next_segment_class in ["parshan", "midrash", "talmud"]:
                        self.set_current_parshan(segment)
                else:
                    #case where this is probably introduction a bunch of comments
                    if segments[i-1][0] == "combined_with_next_line": #several in a row
                        segments[i] = ('combined_with_next_line', segment.text, self.quotation_stack[-1])

                    else:
                        self.intro_to_many_comment_finds[segment.text] += 1
                        self.set_current_parshan(segment)
                        segments[i] = ("combined_with_next_line", segment.text, self.quotation_stack[-1])
            assert self.quotation_stack, "Warning: Quotation stack empty"
        return segments


    def get_term(self, poss_title):
        poss_title = poss_title.strip()
        if poss_title in library.full_title_list('he'):
            return poss_title
        elif Term().load({"titles.text": poss_title}):
            likely_index_title = u"{} על {}".format(poss_title, self.current_sefer)
            if likely_index_title in library.full_title_list('he'):
                return likely_index_title
        return None

    #
    # def look_for_title(self, text):
    #     # cases where this is called are Biblical references outside the parsha such as "Melachim B 3:4"
    #     # or commentary reference with no a_tag such as "Midrash Rabbah 3:4"
    #     if len(text.split()) > 15:
    #         self.index_needs_parsing.add(text)
    #         return text
    #     words = text.split()
    #     poss_title = ""
    #     index = None
    #     for word in words: #iterate over string each time making string longer to look for possible Term or Index match
    #         poss_title += word
    #         index = self.get_term(poss_title)
    #         if index:
    #             text_after_index = text.replace(index, u"", 1).strip()
    #             perek, pasuk = text_after_index.split()[0:2] #just a guess for now that this will be perek and pasuk
    #             perek = getGematria(perek)
    #             pasuk = getGematria(pasuk)
    #             # check that this makes sense
    #             try:
    #                 ref = u"{} {}:{}".format(index, perek, pasuk)
    #                 Ref(ref), u"Pasuk {} is wrong for {} {}".format(pasuk, index, perek)
    #             except InputError:
    #                 try:
    #                     ref = u"{} {}".format(index, perek)
    #                     Ref(ref), u"Perek {} is wrong for {}".format(perek, index)
    #                 except InputError:
    #                     self.index_needs_parsing.add(ref)
    #             return ref
    #         else:
    #             poss_title += " "
    #
    #     self.index_not_found[text] += 1
    #     return text

    """ 

    #logic: if it's perek/pasuk, it's clear you add the sefer and perek pasuk info; if the next is bible and there is no perek pasuk,
    #add the entire thing but make sure it's less than a certain number of words AND that part of it is an index in library
    #if it's parshan/midrash/talmud, a tag gets us title (does it get perek and pasuk ever?)
    if not make sure it's less than a certain number of words, take the whole thing AND assert it is an index in library
    """

    def set_current_parshan(self, segment):
        # need to deal with cases where perek and pasuk are also given
        # create set of all cases found in a tags
        if segment.name == "a":
            a_tag = segment
        else:
            a_tag = segment.find('a')

        if a_tag:
            a_tag_is_entire_comment = len(a_tag.text.split()) == len(segment.text.split())
            a_tag_occurs_in_long_comment = len(segment.text.split()) > 15
        if a_tag:
            if (a_tag_is_entire_comment or a_tag_occurs_in_long_comment):
                # special case is when there is a link and the entirety of the text is a link (check the number of words because there could be a ":" after the link)
                # OR the link occurs in the middle of a long comment where we assume no perek or pasuk is mentioned
                real_title = self.get_term(a_tag.text)
                if not real_title:
                    self.index_not_found[u"{}".format(a_tag.text)] += 1
                    self.quotation_stack.append(u"{} {}".format(a_tag.text, self.current_perek))
                else:
                    self.quotation_stack.append(u"{} {}".format(real_title, self.current_perek))
                if self.current_pasuk:
                    self.quotation_stack[-1] += ":{}".format(self.current_pasuk)
            else:
                # there is a link at the beginning followed by a short string which may be a ref
                num_words_a_tag = len(a_tag.text.split())
                ref_text = " ".join(segment.text.split()[num_words_a_tag:])
                self._get_refs_in_string(ref_text)
        else:
            #every other case: there is no link such as "Bereshit Rabbah Chapter 23"
            self._get_refs_in_string(segment.text)


    def _get_refs_in_string(self, string):
        orig = string
        string = "(" + string + ")"
        words_to_replace = [u"פרשה", u"*", chr(39), u"פרק"]
        for word in words_to_replace:
            string = string.replace(word, u"")
        string = string.replace(u"  ", u" ")
        string = string.strip()
        refs = library.get_refs_in_string(string)
        if refs:
            self.quotation_stack.append(refs[0].normal())
            assert len(refs) is 1
        else:
            self.quotation_stack.append(orig)
            self.index_not_found[orig] += 1


    def set_current_perek_pasuk(self, text):
        if u"פרק" in text:
            perek_pos = text.split().index(u"פרק")
            self.current_perek = getGematria(text.split()[perek_pos+1])
        if u"פסוק" in text:
            pasuk_pos = text.split().index(u"פסוק")
            assert pasuk_pos != -1, "Assumed that pasuk info was here but there isn't any."
            self.current_pasuk = getGematria(text.split()[pasuk_pos+1])
            self.quotation_stack.append(u"{} {}:{}".format(self.current_sefer, self.current_perek, self.current_pasuk))
        else:
            self._get_refs_in_string(text)




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
        sefer = perek_info.split()[0]
        pereks = re.findall(u"פרק\s+(.*?)\s+", perek_info)
        return (sefer, [getGematria(perek) for perek in pereks])



    def download_sheets(self):
        start_after = 274
        for i in self.bereshit_parshiot:
            if int(i) <= start_after:
                continue
            print "downloading {}".format(i)
            response = requests.get("http://www.nechama.org.il/pages/{}.html".format(i))
            print "sleeping"
            time.sleep(1)
            with open("{}.html".format(i), 'w') as f:
                f.write(response.content)


    def load_sheets(self):
        page_missing = u'דף שגיאות'
        for i in self.bereshit_parshiot:
            content = BeautifulSoup(open("{}.html".format(i)), "lxml")
            header = content.find('div', {'id': 'contentTop'})
            if page_missing in header.text:
                continue
            hebrew_year = content.find("div", {"id": "year"}).text.replace(u"שנת", u"")
            roman_year = getGematria(hebrew_year) + 1240
            parsha = content.find("div", {"id": "paging"}).text
            self.current_sefer, self.current_perakim = self.extract_perek_info(content)
            print "Sheet {}".format(i)
            text = content.find("div", {"id": "contentBody"})
            if parsha not in self.sheets:
                self.sheets[parsha] = {}
            assert roman_year not in self.sheets[parsha].keys()
            self.parsha_and_year_to_url[parsha+" "+str(roman_year)] = i
            self.current_url = i
            self.current_perek = self.current_perakim[0]
            self.quotation_stack.append(u"{} {}".format(self.current_sefer, self.current_perek))
            self.sheets[parsha][roman_year] = (hebrew_year, self.current_sefer, self.current_perakim, self.parse_as_text(text))
            pass


    def post_sheets(self):
        pass


if __name__ == "__main__":
    sheets = Sheets()
    #sheets.download_sheets()
    sheets.load_sheets()
    sheets.post_sheets()
    pass

