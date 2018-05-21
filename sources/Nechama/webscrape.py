#encoding=utf-8
import requests
import re
from bs4 import BeautifulSoup, element
from sources.functions import getGematria
import logging
logger = logging.getLogger(__name__)
import django
django.setup()
import urllib2, urllib
from sefaria.model import *
from sources.functions import convertDictToArray, post_index, post_text, post_link, post_sheet
import difflib
from collections import Counter
import time
from data_utilities.util import WeightedLevenshtein
from sefaria.system.exceptions import *

class Sheets:
    def __init__(self):
        self.he_title_project = u"גיליונות נחמה"
        self.en_title_project = "Nechama Leibowitz Source Sheets"
        self.versionTitle = "asdf"
        self.versionSource = "http://nechama.org.il"
        self.table_classes = {}
        self.server = "http://localhost:8000"
        self.bereshit_parshiot = ["1", "2", "30", "62", "84", "148","212","274","302","378","451","488","527","563","570","581","750","787","820","844","894","929","1021","1034","1125","1183","1229","1291","1351","1420"]
        self.sheets = {}
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

        #these two variables keep track of layers of quotations Nechama references...quotations is a list of all quotations
        #and quotation_stack is a stack that we pop when we find a quotation in quotations
        #then we can check the stack later to see if there were any quoations that weren't popped/used
        self.quotations = []
        self.quotation_stack = []
        self.current_ref_in_sefaria = None #when she mentions a ref, what text does the ref correspond to in Sefaria library?
        self.relevant_text = lambda segment: segment if isinstance(segment, element.NavigableString) else segment.text

        self.found = set() #found holds all titles of books we found in the library
        self.index_not_found = Counter() #indexes not found in library
        self.intro_to_many_comment_finds = Counter() #2.html 5th section Shadal
        self.significant_class = lambda class_: True #class_ in ["header", "question"] or "question" in class_



    def parse_as_sheets(self, text):
        pass


    def parse_as_text(self, text):
        sheet_sections = []
        intro_segment = None
        for div in text.find_all("div"):
            if div['id'] == "sheetRemark" and div.text.replace(" ", "") != "": # comment of hers that appears at beginning of section
                intro_segment = div
            elif "ContentSection" in div['id']: #sections within source sheets
                self.current_section += 1
                assert str(self.current_section) in div['id']

                if div.text.replace(" ", "") == "":
                    continue

                # removes nodes with no content
                segments = self.get_children_with_content(div)

                # blockquote is really just its children so get replace it with them
                # and tables need to be handled recursively
                segments = self.check_for_blockquote_and_table(segments, level=2)

                # here is the main logic of parsing
                if intro_segment:
                    segments.insert(0, intro_segment)
                segments = self.classify_segments(segments)

                #assert len(self.quotations) == self.current_pos_in_quotation_stack+1
                #assert 3 > len(self.quotation_stack) > 0
                #if len(self.quotation_stack) >= 2:
                #    segments = self.add_links_from_intro_to_many_comments(segments)
                self.quotation_stack = [u"{} {}".format(self.current_sefer, self.current_perek)]
                self.quotations = [["bible", self.quotation_stack[0]]]
                sheet_sections.append(segments)

        self.quotations = []
        self.quotation_stack = []
        self.current_pos_in_quotation_stack = 0
        self.current_section = 0
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



    def check_for_blockquote_and_table(self, segments, level=2):
        new_segments = []
        tables = ["table", "tr"]
        for i, segment in enumerate(segments):
            if isinstance(segment, element.Tag):
                class_ = segment.attrs.get("class", [""])[0]
            # if self.significant_class(class_):
            #     new_segments.append(segment)
            #     continue
            if segment.name == "blockquote": #this is really many children so add them to list
                new_segments += self.get_children_with_content(segment)
            elif segment.name == "tr" or (self.significant_class(class_) and segment.name == "table"):
                    # if class_ not in self.table_classes:
                    #     self.table_classes[class_] = set()
                    # ste_url = nechama_url = None
                    # self.table_classes[class_].add(self.current_url)
                extra_segments = self.unwrap_HTML_tables(segment)
                new_segments += extra_segments
            else:
                #no significant class and not blockquote or table
                new_segments.append(segment)


        level -= 1
        if level > -1: #go level deeper unless level isn't > 0
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

        #deal with problematic cases first
        if not sefaria_text:
            print "Don't have this text in library."
            return nechama_ref
        if type(sefaria_text[0]) is list: # it's 2-deep
            print "Found 2-deep"
            return nechama_ref


        wl = WeightedLevenshtein()
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
        if max_ratio < 40:
            print self.current_url+".html"+": "+nechama_ref
        else:
            return found_ref


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
        combined_with_prev_line = None
        important_classes = ["parshan", "midrash", "talmud", "bible", "commentary"]
        for i, segment in enumerate(segments):
            if isinstance(segment, element.Tag) and segment.has_attr("class"):
                segment_class = segment.attrs["class"][0]
                text = segment.text.replace("\n", "").replace("\r", "")
                if combined_with_prev_line: #i.e.: "Pasuk 5" is the previous line which gets combined with the current line that has Pasuk 5's content
                    text = combined_with_prev_line + "\n" + text
                    combined_with_prev_line = None
                if segment_class == "header" or "question" in segment_class:
                    ref = self.current_parsha_ref[1] #was self.quotations[0][1]
                    segments[i] = ("nechama", text, ref)
                elif segment_class in important_classes:
                    quote = self.quotations[-1]
                    #self.quotation_stack.pop()
                    category, ref = quote
                    assert category == segment_class or category == "bible"
                    # if segments[i-1] == "combined and linked":
                    #    self.check_ref_text_in_sefaria(text, ref)
                    segments[i] = (segment_class, text, ref)
                else:
                    # must be either header, parshan, bible, or question
                    print "Found other class...{}".format(segment_class)
            else:
                # if there is no class, then...
                # it is either setting perek/pasuk info
                # or telling us what the next parshan is
                # OR just a comment,
                # if this comment or next are NavigableStrings, just treat this comment as ordinary comment
                # also if the next comment isn't parshan or bible, just treat it as ordinary comment
                # otherwise, try to set perek/pasuk or parshan from it

                #assert segments[i+1], "Assumed that this cannot be the last in the section/sheet, but it is."
                next_comment_parshan_or_bible = ""
                this_comment_could_be_ref = i < len(segments) - 1 and isinstance(segments[i+1], element.Tag) and isinstance(segments[i], element.Tag)
                if this_comment_could_be_ref:
                    next_comment_parshan_or_bible = "class" in segments[i+1].attrs.keys() and segments[i+1].attrs["class"][0] in important_classes
                relevant_text = self.relevant_text(segment)
                if not next_comment_parshan_or_bible:
                    segments[i] = ('nechama', relevant_text, self.current_parsha_ref[1]) #was self.quotations[0][1]
                else:
                    a_tag_is_entire_comment = False #this means there is supposed to be a match if True because comment is clearly a reference to a commentator and not just about the commentator
                    next_segment_class = segments[i+1].attrs["class"][0]
                    is_torah_ref = self.set_current_perek_pasuk(relevant_text, next_segment_class)
                    is_parshan_ref = False
                    if not is_torah_ref:
                        is_parshan_ref, a_tag_is_entire_comment = self.set_current_parshan(segment, relevant_text,  next_segment_class)
                    if is_parshan_ref or is_torah_ref:
                        combined_with_prev_line = relevant_text
                        segments[i] = "combined and linked"
                    elif a_tag_is_entire_comment:
                        combined_with_prev_line = relevant_text
                        segments[i] = relevant_text
                    elif not is_parshan_ref and not is_torah_ref:
                        segments[i] = ('nechama', relevant_text, self.current_parsha_ref[1])
                # else:
                #     #case where this is probably introduction a bunch of comments
                #     if segments[i-1][0] == "combined_with_next_line":
                #         # several in a row, so use previous quotation stack
                #         segments[i] = ('combined_with_next_line', segment.text, self.quotations[-1][1])
                #
                #     else:
                #         # this is the first one (or only one) which probably has parshan info
                #         self.set_current_parshan(segment, "") #pass empty next_segment_class in this case as it doesn't matter
                #                                               #because it will never be accessed since it opens a section of comments
                #                                               #and not a specific comment
                #         segments[i] = ("combined_with_next_line", segment.text, self.quotations[-1][1])
                #         self.intro_to_many_comment_finds[segments[i]] += 1
            #assert self.quotations, "Warning: Quotation stack empty"
        return segments


    def get_term(self, poss_title):
        #return the english index name corresponding to poss_title or None
        poss_title = poss_title.strip()
        if poss_title in self._term_cache:
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
            #first see that the Ref exists
            try:
                category_and_ref[1] = Ref(ref)
                #at this point we know we have a real Ref so get text
                sefaria_text = category_and_ref[1].text('he').text
                category_and_ref[1] = category_and_ref[1].normal()
                self.current_ref_in_sefaria = (sefaria_text, category_and_ref[1])
            except InputError as e:
                #try iterating over current_alt_titles and seeing if any allow us to create a Ref that exists so each time we call the function with try_alt_titles of False
                #so that it does not generate an infinite loop
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

    def remove_from_quotation_stack(self):
        pass

    """ 

    #logic: if it's perek/pasuk, it's clear you add the sefer and perek pasuk info; if the next is bible and there is no perek pasuk,
    #add the entire thing but make sure it's less than a certain number of words AND that part of it is an index in library
    #if it's parshan/midrash/talmud, a tag gets us title (does it get perek and pasuk ever?)
    if not make sure it's less than a certain number of words, take the whole thing AND assert it is an index in library
    """

    def set_current_parshan(self, segment, relevant_text, next_segment_class):
        ##return tuple of boolean values -- first one whether we found anything, second one whether we found a tag or u tag indicating there IS a commentator
        #first just see if segment.text is a ref -- if it is, _get_refs_in_string adds it
        #then exit set_current_parshan
        a_tag_occurs_in_long_comment = a_tag_is_entire_comment = False
        if self._get_refs_in_string([relevant_text], next_segment_class, add_if_not_found=False):
            return (True, a_tag_is_entire_comment)

        #segment.text isn't a Ref, so now look for a title in a_tag.text
        if segment.name == "a":
            a_tag = segment
        else:
            a_tag = segment.find('a')

        if not a_tag:
            a_tag = segment.find("u")

        if a_tag:
            a_tag_is_entire_comment = len(a_tag.text.split()) == len(segment.text.split())
            a_tag_occurs_in_long_comment = len(segment.text.split()) > 15
        if not a_tag or not (a_tag_is_entire_comment or a_tag_occurs_in_long_comment):
            #looking for a ref...
            #b/c/ either there's no a_tag at all OR there is an a_tag but it is only part of the comment and it's not a long comment so it MIGHT be a ref like (<a>Rashi</a>, Perek B)
            return (self._get_refs_in_string([segment.text], next_segment_class, add_if_not_found=True), a_tag_is_entire_comment)
        else:
            #no ref...
            # this case is when we know there's no ref being mentioned so try to examine the a_tag
            # special case is when there is a link and the entirety of the text is a link (check the number of words because there could be a ":" after the link)
            # OR the link occurs in the middle of a long comment where we assume no perek or pasuk is mentioned

            real_title = self.get_term(a_tag.text)

            if not real_title:
                self.index_not_found[u"{}".format(a_tag.text)] += 1
                self.add_to_quotation_stack(self.current_parsha_ref)
                #self.add_to_quotation_stack([next_segment_class, u"{} {}".format(a_tag.text, self.current_perek)], in_sefaria=False)
            else:
                if self.current_pasuk:
                    self.add_to_quotation_stack([next_segment_class, u"{} {}:{}".format(real_title, self.current_perek, self.current_pasuk)])
                else:
                    self.add_to_quotation_stack([next_segment_class, u"{} {}".format(real_title, self.current_perek)])
            # last_quotation_ref = self.quotations[-1][1]
            # last_quotation_ref_just_index = last_quotation_ref.split()[0] # i.e. trim "3:17" off ref
            # if self.current_pasuk and last_quotation_ref_just_index not in self.current_alt_titles: #second check is there b/c when we can't find quotation, we fall back on current_parsha_ref like Genesis 3:2
            #     self.quotations[-1][1] += ":{}".format(self.current_pasuk)
            #     self.quotation_stack[-1] += ":{}".format(self.current_pasuk)
            return (real_title, a_tag_is_entire_comment)
            # else:
            #     # there is a link at the beginning followed by a short string which may be a ref
            #     num_words_a_tag = len(a_tag.text.split())
            #     ref_text = " ".join(segment.text.split()[num_words_a_tag:])
            #     self._get_refs_in_string([ref_text, segment.text], next_segment_class, add_if_not_found=True)



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
                return True
            else:
                not_found.append(orig)
        if len(not_found) == len(strings) and add_if_not_found: # nothing found
            self.index_not_found[strings[-1]] += 1
            #self.add_to_quotation_stack([next_segment_class, strings[-1]], in_sefaria=False)
            self.add_to_quotation_stack(self.current_parsha_ref)
        return False


    def set_current_perek_pasuk(self, text, next_segment_class):
        text = text.replace(u"פרקים", u"Perek").replace(u"פרק", u"Perek").replace(u"פסוקים", u"Pasuk").replace(u"פסוק", u"Pasuk").strip()
        digit = re.compile(u"^.{1,2}\)").match(text)
        # if next_segment_class == "parshan":e
        #     sefer = u"Parshan on {}".format(self.current_sefer)
        # elif next_segment_class == "bible":
        sefer = self.current_sefer

        if digit:
            text = text.replace(digit.group(0), "").strip()
        perek_pasuk = re.compile(u"(Perek .{1,8})?(Pasuk .{1,8}|,.{1,8})") #group 1 is Perek X and group 2 is Pasuk Y (or ", Y" without the word Pasuk)
        match = perek_pasuk.match(text)
        if match:
            second_group = match.group(1) # should be Perek
            if second_group:
                self.current_perek = getGematria(second_group.split()[-1])
            self.current_pasuk = getGematria(match.group(2).split()[-1].split("-")[0]) #last word in match is Pasuk and if there is a range "3-4", take just "3"
            self.current_parsha_ref = [next_segment_class, u"{} {}:{}".format(sefer, self.current_perek, self.current_pasuk)]
            self.add_to_quotation_stack(self.current_parsha_ref)
            return True
        else:
            just_perek = re.compile(u"Perek (.{1,8})").match(text)
            if just_perek:
                perek = just_perek.group(1)
                self.current_perek = getGematria(perek)
                self.current_pasuk = None
                self.current_parsha_ref = [next_segment_class, u"{} {}".format(sefer, self.current_perek)]
                self.add_to_quotation_stack(self.current_parsha_ref)
                return True
            else:
                return False




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
        pereks = re.findall(u"Perek\s+(.)\s?", perek_info)
        return (sefer, [getGematria(perek) for perek in pereks])



    def download_sheets(self):
        start_after = 274
        for i in self.bereshit_parshiot:
            if int(i) <= start_after:
                continue
            print "downloading {}".format(i)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
            response = requests.get("http://www.nechama.org.il/pages/{}.html".format(i), headers=headers)
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
            self.current_sefer = library.get_index(self.current_sefer)
            self.current_alt_titles = self.current_sefer.nodes.get_titles('en')
            self.current_sefer = self.current_sefer.title
            print "Sheet {}".format(i)
            text = content.find("div", {"id": "contentBody"})
            if parsha not in self.sheets:
                self.sheets[parsha] = {}
            assert roman_year not in self.sheets[parsha].keys()
            self.year_to_url[roman_year] = i
            self.current_url = i
            self.current_perek = self.current_perakim[0]
            self.current_pasuk = None
            self.quotations = []
            self.current_pos_in_quotation_stack = 0
            self.quotation_stack = []
            self.current_parsha_ref = ["bible", u"{} {}".format(self.current_sefer, self.current_perek)]
            self.add_to_quotation_stack(self.current_parsha_ref)
            self.sheets[parsha][roman_year] = (self.current_url, hebrew_year, self.current_sefer, self.current_perakim, self.parse_as_text(text))
            pass


    def get_text_links_and_sources(self, text_list, parsha, year):
        """
                               segments[i] = "combined and linked"
                    elif a_tag_is_entire_comment:
                        combined_with_prev_line = relevant_text
                        segments[i] = relevant_text
        :param text_list:
        :param parsha:
        :param year:
        :return:
        """
        links = []
        sources = []
        important_clases = ["parshan", "midrash", "talmud", "bible", "commentary"]
        for i, section in enumerate(text_list):
            section = [el for el in text_list[i] if isinstance(el, tuple)]
            for j, segment in enumerate(section):
                type, comment, comm_ref = segment
                if type == "nechama":
                    source = {"outsideText": comment, "node": j+1}
                elif type in important_clases:
                    heRef = Ref(comm_ref).he_normal()
                    source = {"node": j+1, "ref": comm_ref, "heRef": heRef,
                              "text": {
                                         "en": "", "he": comment
                                      }
                              }
                else:
                    raise InputError
                sources.append(source)
                term = Term().load({"titles.text": parsha})
                assert term, u"{} doesn't have term".format(parsha)
                nechama_ref = u"{}, {} {}".format(self.en_title_project, term.name, year)
                link = {"refs": [
                            nechama_ref,
                            comm_ref
                        ],
                        "type": "commentary",
                        "auto": True,
                        "generated_by": "nechama_linker"
                        }
                links.append(link)
                section[j] = comment
            text_list[i] = section

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
            "categories": ["Tanakh", "Commentary"]
        }
        post_index(index, server=self.server)


    def post_index(self):
        self.create_index()
        nechama_text = {}
        nechama_sheet = {}
        all_links = []
        important_classes = ["parshan", "midrash", "talmud", "bible", "commentary"]
        for parsha, sheets_by_year in self.sheets.items():
            term = Term().load({"titles.text": parsha})
            assert term, u"{} doesn't have term".format(parsha)
            parsha = term.name
            nechama_text[parsha] = {}
            nechama_sheet[parsha] = {}
            for en_year, sheet in sheets_by_year.items():
                url, he_year, sefer, perakim, text_tuples = sheet
                text, links, sources = self.get_text_links_and_sources(text_tuples, parsha, en_year)
                all_links += links
                nechama_text[parsha][he_year] = text
                self.prepare_sheet("{} {} {}".format(self.en_title_project, parsha, en_year), sources)
            nechama_text[parsha] = convertDictToArray(nechama_text[parsha])
            send_text = {
                "text": nechama_text[parsha],
                "language": "he",
                "versionTitle": self.versionTitle,
                "versionSource": self.versionSource
            }
            post_text(u"{}, {}".format(self.en_title_project, parsha), send_text, server=self.server)
        post_link(all_links, server=self.server)
        # for year, sheet in enumerate(nechama_text[parsha]):
        #     if year < 1941:
        #         continue
        #     for section_n, section in enumerate(sheet):
        #         post_text(u"{}, {} {}:{}".format(self.en_title_project, parsha, year+1, section_n+1), section, server=self.server)


    def prepare_sheet(self, title, sources):
       print title
       sheet_json = {}
       sheet_json["status"] = "public"
       sheet_json["title"] = title
       sheet_json["sources"] = [sources]
       sheet_json["options"] = {"numbered": 0,"assignable": 0,"layout": "sideBySide","boxed": 0,"language": "bilingual","divineNames": "noSub","collaboration": "none", "highlightMode": 0, "bsd": 0,"langLayout": "heRight"}
       post_sheet(sheet_json, server="http://ste.sefaria.org")

if __name__ == "__main__":
    sheets = Sheets()
    #sheets.download_sheets()
    sheets.load_sheets()
    sheets.post_index()
    pass



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