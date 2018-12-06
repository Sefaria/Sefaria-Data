#encoding=utf-8

import django
django.setup()

import requests
import re
import os
from sources.functions import getGematria
from sefaria.model import *
from segments import *
from sefaria.system.database import db
from sefaria.system.exceptions import InputError
from collections import OrderedDict, Counter
from bs4 import BeautifulSoup, element

import numpy
from time import sleep
import bleach
import shutil
from sources.functions import *
import unicodedata
from sefaria.utils.hebrew import strip_cantillation
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from data_utilities.util import WeightedLevenshtein
import datetime
import traceback


class Sheet(object):

    def __init__(self, html, parasha, title, year, perek_info):
        self.html = html
        self.title = title
        self.parasha = parasha
        self.en_parasha = parser.en_parasha
        self.sefer, self.perakim, self.pasukim = self.extract_perek_info(perek_info)
        self.en_sefer = library.get_index(self.sefer).title
        if self.en_sefer != parser.en_sefer:
            parser.en_sefer = self.en_sefer
            parser.populate_term_mapping_and_id_table()
        self.he_year = re.sub(u"שנת", u"", year).strip()
        self.year = getGematria(self.he_year) + 5000  # +1240, jewish year is more accurate
        self.en_year = getGematria(self.he_year) + 1240
        #self.pasukim = self.get_ref(ref)  # (re.sub(u"(פרק(ים)?|פסוק(ים)?)", u"", ref).strip())
        self.sheet_remark = u""
        self.header_links = None  # this will link to other  nechama sheets (if referred).
        self.quotations = []  # last one in this list is the current ref
        self.current_section = 0
        self.div_sections = [] # BeautifulSoup objects that will eventually become converted into Section objects stored in self.sections
        self.sections = []
        self.sources = []
        self.links_to_other_sheets = False


    # def flip_ref_parasha_to_haftarah(self, ref, haftarah):
    #     haftarah_index = Ref(haftarah).index.title
    #     try:
    #         base_ref = ref.split(" on ")[1] if " on " in ref else ref #strip "Rashi on Genesis 2" to "Genesis 2"
    #         orig_index = library.get_index(" ".join(base_ref.split()[0:-1])) # now strip "Genesis 2" to "Genesis"
    #     except BookNameError:
    #         return ref
    #     orig_index = orig_index.title
    #     ref = ref.replace(orig_index, haftarah_index)
    #     return ref



    def create_sheetsources_from_objsource(self):
        # first source in the sheet is the sheet remark
        if self.sheet_remark:
            parser.word_count += len(self.sheet_remark)
            self.sources.append({"outsideText": self.sheet_remark,
             "options": {
                 "indented": "indented-1",
                 "sourceLayout": "",
                 "sourceLanguage": "hebrew",
                 "sourceLangLayout": ""
             }
             })
        for isection, section in enumerate(self.sections):
            self.sources.extend(self.create_sheetsources_from_sections(section.segment_objects)) # vs section and than getting the section.segment_objects latter in create_sheetsources_from_sections function





    def create_sheetsources_from_sections(self, segment_objects):
        sheets_sources = []
        guess_ref = u""
        guess_parshan = 0
        for isegment, segment in enumerate(segment_objects):
            if not segment:
                continue
            if isinstance(segment, Source):# or isinstance(segment, Nested):
                orig_ref = segment.ref
                parser.trying_pm = 0
                segment.guess_ref = guess_ref
                if segment.parshan_id:
                    guess_parshan = segment.parshan_id
                success = parser.try_parallel_matcher(segment, guess_ref, guess_parshan)
                if not success and segment.snunit_ref:  # take 2
                    success = parser.try_parallel_matcher(segment, segment.snunit_ref.normal(), guess_parshan)
                # look at guess ref, maybe it was ignored because there was a Sefaria ref first
                if not success:
                    temp =segment.ref
                    segment.ref = guess_ref
                    success = parser.try_parallel_matcher(segment, guess_ref, guess_parshan)
                    if not success:
                        segment.ref = temp
                if success:
                    if Ref(segment.ref).is_commentary():
                        if re.search(u".*(?:on|,)\s((?:[^:]*?):(?:[^:]*)):?", segment.ref):
                            r_base = Ref(re.search(u".*(?:on|,)\s((?:[^:]*?):(?:[^:]*)):?", segment.ref).group(1))
                            guess_ref = r_base.normal()
                    else:
                        guess_ref = segment.ref # if base text keep for the next source segment
                elif not success:  # not success couldn't find matching text
                    success2 = False
                    # try a level up
                    temp = parser.mode
                    if segment.ref:
                        try:
                            segment.ref = Ref(segment.ref).top_section_ref().normal()
                            parser.mode = 'fast'
                            success2 = parser.try_parallel_matcher(segment)
                        except InputError:
                            pass
                    parser.mode = temp
                    if success2 and segment.segment_class in [u'midrash', u'parshan'] and Ref(
                            segment.ref).primary_category == u'Tanakh':
                        # mustbe a pm mistake go back to orig
                        segment.ref = segment.about_source_ref
                    elif not success2:
                        segment.ref = segment.about_source_ref
                        # if orig_ref:
                        #     if segment.segment_class in [u'midrash', u'parshan'] and Ref(orig_ref).primary_category != u'Tanakh':
                        #         segment.ref = orig_ref
                        #     # segment.ref = orig_ref # todo: !! find where to return the lost data about the commentators name info from, maybe about_source_ref?
                        #     else:
                        #         segment.ref = segment.about_source_ref
                        #         # segment.about_source_ref += Ref(orig_ref).normal('he')
                        #     pass
                        # else:
                        #     segment.ref = segment.about_source_ref
                    if success and segment.segment_class in [u'midrash', u'parshan'] and Ref(segment.ref).primary_category == u'Tanakh':
                        # mustbe a pm mistake go back to orig
                        segment.ref = segment.about_source_ref
                seg_sheet_source = segment.create_source()
            elif isinstance(segment, Nested):
                if segment.question:
                    q_source = Question(question=segment.question)
                    if isinstance(segment.segment_objs[0], Source):
                        q_source.q_text = segment.segment_objs[0].ref
                        segment.segment_objs[0].ref = q_source.format()

                        q_source.q_text = segment.segment_objs[0].about_source_ref
                        segment.segment_objs[0].about_source_ref = q_source.format()
                    else:
                        q_source.q_text = segment.segment_objs[0].text
                        segment.segment_objs[0].text = q_source.format()
                seg_sheet_source = self.create_sheetsources_from_sections(segment.segment_objs)

            else:
                seg_sheet_source = segment.create_source()
            self.add_to_word_count(seg_sheet_source)
            sheets_sources.extend(seg_sheet_source if isinstance(seg_sheet_source, list) else [seg_sheet_source])
            # print u"done with seg {}".format(isegment)
        return sheets_sources



    def add_to_word_count(self, seg):
        if isinstance(seg, list):
            for x in seg:
                self.add_to_word_count(x)
        else:
            seg_text = seg["outsideText"] if "outsideText" in seg.keys() else seg["text"]["he"]
            parser.word_count += len(seg_text.split(" "))


    def check_haftarot(self, segment):
        orig_ref = segment.ref
        for section in parser.parasha_and_haftarot:
            new_ref = self.flip_ref_parasha_to_haftarah(segment.ref, section)
            if new_ref != segment.ref:
                segment.ref = new_ref
                success = parser.try_parallel_matcher(segment)
                if success:
                    break
                else:
                    segment.ref = orig_ref


    def prepare_sheet(self, add_to_title="", post=False):
       sheet_json = {}
       sheet_json["status"] = "public" #"private" #
       sheet_json["group"] =u"גיליונות נחמה"#"Nechama Leibowitz' Source Sheets"
       sheet_json["title"] = u'{} - {} {}'.format(self.title, re.search('(\d+)\.', self.html).group(1), add_to_title)
       # sheet_json["title"] = u"{} {} - {}".format(self.parasha, self.he_year, self.title)
       sheet_json["summary"] = u"{} ({})".format(self.en_year, self.he_year)
       sheet_json["sources"] = self.sources
       sheet_json["options"] = {"numbered": 0, "assignable": 0, "layout": "sideBySide", "boxed": 0, "language": "hebrew", "divineNames": "noSub", "collaboration": "none", "highlightMode": 0, "bsd": 0, "langLayout": "heRight"}

       if "-" in self.en_parasha:
           sheet_json["tags"] = [unicode(self.en_parasha.split("-")[0]), unicode(self.en_parasha.split("-")[-1])]
           assert Term().load({"name": self.en_parasha.split("-")[0]})
           assert Term().load({"name": self.en_parasha.split("-")[-1]})
       else:
           sheet_json["tags"] = [unicode(self.en_parasha)]
           assert Term().load({"name": self.en_parasha})
       if self.links_to_other_sheets:
           parser.sheets_linked_to_sheets.append((sheet_json["title"], sheet_json["summary"], sheet_json["tags"]))
       if post:
           post_sheet(sheet_json, server=parser.server)



    def extract_perek_info(self, perek_info):
        def get_pasukim_for_perek(sefer, perek):
            en_sefer = library.get_index(sefer).title
            return str(len(Ref(u"{} {}".format(en_sefer, perek)).all_segment_refs()))

        #three formats: Perek 2; Perek 2, Pasuk 3-9; Perek 2, 4 - Perek 3, 2 (last one may lose pasuk info as well
        sefer = perek_info.split()[0]
        try:
            en_sefer = library.get_index(sefer).title
        except BookNameError:
            sefer = " ".join(perek_info.split()[0:2]) # For Melachim Bet
            en_sefer = library.get_index(sefer).title
        perek_info = perek_info.replace(u"פרקים", u"Perek").replace(u"פרק", u"Perek").replace(u"פסוקים", u"Pasuk").replace(u"פסוק", u"Pasuk").strip()
        perek_info = perek_info.replace(sefer, u"")
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
            pasuks = re.findall(u"Pasuk\s+(.{1,18})\s?", perek_info)[0].split(" - ")
            for p, pasuk in enumerate(pasuks):
                pasuks[p] = getGematria(pasuk)
            if len(pasuks) is 2:
                pasuks = range(pasuks[0], pasuks[1]+1)
                pasuks = Ref(en_sefer+" "+pereks[0]+":"+str(pasuks[0])+"-"+str(pasuks[-1]))
            else:
                assert len(pasuks) is 1
                pasuks = Ref(en_sefer + " " + pereks[0] + ":" + str(pasuks[0]))
        else: #first case
            pereks = re.findall(u"Perek\s+(.{1,3})\s?", perek_info)
            assert len(pereks) is 1
            pereks = [str(getGematria(pereks[0]))]
            pasuks = []
            last_pasuk = get_pasukim_for_perek(sefer, pereks[0])
            pasuks = Ref(en_sefer+" "+pereks[0]+":1-"+last_pasuk)

        return (sefer, pereks, pasuks)

    def get_ref(self, he_ref):
        # he_ref = re.sub(u"(פרק(ים)?|פסוק(ים)?)", u"", he_ref).strip()
        # split = re.split()
        try:
            r = Ref(he_ref)
        except InputError:
            return None
        return r

    def parse_as_text(self):
        """
        this method loops over the bs tag obj of the sections and creates Section() objs from them
        and then loops over Section objs crerated to init the list of Segment() objs
        :return:
        """

        # intro_segment = intro_tuple = None

        # init
        for div in self.div_sections:
            self.current_section += 1
            new_section = Section(self.current_section, self.perakim, self.pasukim, soupObj=div)
            assert str(self.current_section) in div['id']
            self.sections.append(new_section)

        # init Segment() obj from bs_objs in each section
        for section in self.sections:
            section.add_segments(section.soupObj)


class Section(object):

    def __init__(self, number, perakim, pasukim, soupObj):
        self.soupObj = soupObj
        self.number = number  # which number section am I
        self.possible_perakim = perakim  # list of perakim: the assumption is that any perek referenced will be in this list
        self.possible_pasukim = pasukim  # Ref range: the assumption is that any pasuk referenced will be inside the range
        self.letter = ""
        self.title = ""
        self.segment_objects = []  # list of Segment objs
        self.RT_Rashi = False
        self.current_parsha_ref = ""
        self.current_perek = self.possible_perakim[0]
        self.current_pasuk = self.possible_pasukim.sections[-1] #the lowest pasuk in the range
        self.has_nested = []

    @staticmethod
    def get_tags(segment):

        if isinstance(segment,element.Tag):
            return [t for t in segment.contents if isinstance(t, element.Tag)]
        elif isinstance(segment,list):
            return [t for t in segment if isinstance(t, element.Tag)]
        else:
            return None

    def add_segments(self, div):

        # removes nodes with no content
        soup_segments = self.get_children_with_content(div)
        for segment in soup_segments:
            class_ = ""
            if isinstance(segment, element.Tag):
                class_ = segment.attrs.get("class", [""])[0]
            if segment.name == "table" and class_ == "RT_RASHI":
                self.RT_Rashi = True
        # blockquote is really just its children so get replace it with them
        # and tables  need to be handled recursively
        # soup_segments = self.check_for_blockquote_and_table(soup_segments)

        # create Segment objects out of the BeautifulSoup objects
        self.classify_segments(soup_segments) #self.segment_objects += self.classify_segments(soup_segments)
        prev_source = None
        new_segment_objects = []
        for i, obj in enumerate(self.segment_objects):
            if isinstance(obj, Source):
                prev_source = obj
            elif isinstance(obj, Text): # and isinstance(self.segment_objects[i-1], Source):
                poss_new_source = None
                if prev_source:
                    poss_new_source = prev_source.add_text(obj.sp_segment, obj.segment_class)
                elif obj.ref_guess:
                    orig_source = Source(obj.ref_guess)
                    poss_new_source = orig_source.add_text(obj.sp_segment)
                else:
                    pass #todo

                if poss_new_source:
                    new_segment_objects.append(poss_new_source)
                else:
                    new_segment_objects.append(prev_source)
            else:
                new_segment_objects.append(obj)
        self.segment_objects = new_segment_objects
        header = filter(lambda x: isinstance(x, Header), self.segment_objects)[0]
        self.title = header.header_text
        self.letter = header.letter
        self.segment_objects = self.flatten_our_section()
        return



    def classify_segments(self, soup_segments):
        """
        Classifies each segments based on its role such as "question", "header", or quote from "bible"
        and then sets each segment to be a tuple that tells us in order:
        who says it, what do they say, where does it link to
        If Nechama makes a comment:
        ("Nechama", text, "")
        If Rashi:
        ("Rashi", text, ref_to_rashi)
        :param soup_segments:
        :return:
        """
        nesnested_lst = []
        current_source = None
        nested_candidates = {} # OrderedDict() # this is a Dict of nested obj, and the q will be do we wan't them as nested or as originals.
        if isinstance(soup_segments, list):
            for i, segment in enumerate(soup_segments):
                sheet_segment = self.classify(segment, i, soup_segments)
                if sheet_segment:
                    self.segment_objects.append(sheet_segment)
            return  # self.segment_objects
        elif isinstance(soup_segments, Nested): #should be the only other possible answer maybe just "else:" here?
            for i, segment in enumerate(soup_segments.obj):
                sheet_segment = self.classify(segment, i, soup_segments.obj)
                if sheet_segment:
                    nesnested_lst.append(sheet_segment)
            return nesnested_lst

    def classify(self, sp_segment, i, soup_segments):
        """

        :param sp_segment: beutiful soup <tag> to classify into our obj and Nested
        :return: our obj (or Nested)
        """

        relevant_text = self.format(self.relevant_text(sp_segment))  # if it's Tag, tag.text; if it's NavigableString, just the string
        if Header.is_header(sp_segment):
            return Header(sp_segment)  # self.segment_objects.append(Header(segment))
        elif Question.is_question(sp_segment):
            nested_seg = Question.nested(sp_segment)
            if nested_seg:  # todo: so we know that this is a Nested Question! what to do with this info?
                return Nested(Nested.is_nested(sp_segment), section=self, question=Question(sp_segment))
            else:
                return Question(sp_segment)
        elif Table.is_table(sp_segment):  # these tables we want as they are so just str(segment)
            return Table(sp_segment)
        elif Source.is_source_text(sp_segment, parser.important_classes):
        # this is a comment by a commentary, bible, or midrash that should be added as text to a Source created previously already or we can derive it's Source
            segment_class = sp_segment.attrs["class"][0]  # is it source, bible, or midrash?
            try:
                source_guess = [x for x in self.segment_objects if (isinstance(x, Source) and x.current)][-1]
                source_guess_ref = source_guess.ref
            except Exception:
                source_guess_ref = None
            # current_source = [x for x in self.segment_objects if (isinstance(x, Source) and x.current)][-1]
            # current_source.add_text(sp_segment, segment_class)
            # return current_source
            return Text(sp_segment, segment_class, ref_guess=source_guess_ref)
        elif Nested.is_nested(sp_segment):
            return Nested(Nested.is_nested(sp_segment), section=self)
        elif Nechama_Comment.is_comment(soup_segments, i, parser.important_classes):  # above criteria not met, just an ordinary comment
            return Nechama_Comment(relevant_text)  # self.segment_objects.append(Nechama_Comment(relevant_text))
        else:  # maybe a Source Ref - so parse it or maybe is a nested blockqute or table - so return it's important children
            # next_segment_class = (soup_segments[i + 1].attrs["class"][0],None if "id" not in soup_segments[i + 1].attrs.keys() else soup_segments[i + 1].attrs["id"])  # get the class of this ref and it's comment
            # next_segment_class = ["parshan"]
            # current_source = self.parse_ref(sp_segment, relevant_text, next_segment_class)
            # current_source.current = True
            # return current_source
            try:
                next_segment_class = (soup_segments[i + 1].attrs["class"][0],
                                  None if "id" not in soup_segments[i + 1].attrs.keys() else soup_segments[i + 1].attrs[
                                      "id"])  # get the class of this ref and it's comment
                # next_segment_class = ["parshan"]
                # creates a Source() obj
                current_source = self.parse_ref(sp_segment, relevant_text, next_segment_class)
                current_source.current = True
                return current_source
            except (KeyError, IndexError):
                nested_list = Nested.is_nested(sp_segment)
                if nested_list:
                    return Nested(nested_list)

    def look_at_next_segment(self):
        pass

    def get_term(self, poss_title):
        # return the english index name corresponding to poss_title or None
        poss_title = poss_title.strip().replace(":", "")

        # already found it
        if poss_title in parser._term_cache:
            return parser._term_cache[poss_title]
        # this title is unusual so look in term_mapping for it
        if poss_title in parser.term_mapping:
            parser._term_cache[poss_title] = parser.term_mapping[poss_title]
            return parser._term_cache[poss_title]
        if [re.search(title, poss_title) for title in parser.has_parasha] != [None]:
            poss_title = self.ignore_parasha_name(poss_title)
        term = Term().load({"titles.text": poss_title})
        if poss_title in library.full_title_list('he'):
            parser._term_cache[poss_title] = library.get_index(poss_title).title
            return parser._term_cache[poss_title]
        elif term:
            term_name = term.name
            likely_index_title = u"{} on {}".format(term_name, parser.en_sefer)
            if likely_index_title in library.full_title_list('en'):
                parser._term_cache[poss_title] = likely_index_title
                return parser._term_cache[poss_title]
        parser._term_cache[poss_title] = None
        return None

    def ignore_parasha_name(self, string):
        parasha_found = [x in string for x in library.get_term_dict('he').keys()]
        if parasha_found:
            return re.sub(parasha_found[0], u"", string)
        return string

    def get_a_tag_from_ref(self, segment, relevant_text):
        starts_perek_or_pasuk = lambda x: (x.startswith(u"פרק ") or x.startswith(u"פסוק ") or
                                x.startswith(u"פרקים ") or x.startswith(u"פסוקים "))

        if segment.name == "a":
            a_tag = segment
            snunit_ref = Section.exctract_pasuk_from_snunit(a_tag)
        else:
            all_a_tag = segment.findAll('a')
            if all_a_tag:
                a_tag = all_a_tag[0]
                snunit_ref = Section.exctract_pasuk_from_snunit(a_tag)
                if len(all_a_tag)>1:
                    print "len all_a_tags = {}, a_tag = {}, next = {}".format(len(all_a_tag),all_a_tag[0], all_a_tag[1])
                    for a in all_a_tag:
                        snr = Section.exctract_pasuk_from_snunit(a)
                        if snr:
                            snunit_ref = Section.exctract_pasuk_from_snunit(a)
            else: # there is no a_tag
                return (False, False, False, False)
        real_title = ""

        # if a_tag and segment.find("u") and a_tag.text != segment.find("u").text: #case where
        a_tag_is_entire_comment = False
        if a_tag and a_tag.attrs and 'href' in a_tag.attrs and re.match('javascript:mypopup\((\d*)\)', a_tag["href"]):
            parshan_id = re.match('javascript:mypopup\((\d*)\)', a_tag["href"]).group(1)
            real_title = parser.parshan_id_table[parshan_id]
        elif a_tag:
            a_tag_is_entire_comment = len(a_tag.text.split()) == len(segment.text.split())
            real_title = self.get_term(a_tag.text)
        elif relevant_text in parser.term_mapping:
            real_title = parser.term_mapping[relevant_text]
        elif [term for term in parser.term_mapping.keys() if re.search(term, relevant_text)]: #try again to use the mapping
            in_mapping = [term for term in parser.term_mapping.keys() if re.search(term, relevant_text)]
            found_in_mapping = in_mapping[0] if in_mapping else None
            real_title = parser.term_mapping[found_in_mapping]
        if not real_title and self.RT_Rashi:  # every ref in RT_Rashi is really to Rashi
            real_title = "Rashi on {}".format(parser.en_sefer)
        return (real_title, a_tag, a_tag_is_entire_comment, snunit_ref)

    def parse_ref(self, segment, relevant_text, next_segment_info):
        next_segment_class = next_segment_info[0]

        real_title, found_a_tag, a_tag_is_entire_comment, snunit_ref = self.get_a_tag_from_ref(segment, relevant_text)
        found_ref_in_string = ""

        # check if it's in Perek X, Pasuk Y format and set perek and pasuk accordingly
        is_tanakh = (relevant_text.startswith(u"פרק ") or relevant_text.startswith(u"פסוק ") or
                     relevant_text.startswith(u"פרקים ") or relevant_text.startswith(u"פסוקים "))
        is_perek_pasuk_ref, new_perek, new_pasuk = self.set_current_perek_pasuk(found_a_tag, relevant_text, next_segment_class, is_tanakh)


        # now create current_source based on real_title or based on self.current_parsha_ref
        if real_title:  # a ref to a commentator that we have in our system
            if new_pasuk:
                current_source = Source(u"{} {}:{}".format(real_title, new_perek, new_pasuk), next_segment_class)
            else:
                current_source = Source(u"{} {}".format(real_title, new_perek), next_segment_class)
        elif snunit_ref:
            current_source = Source(snunit_ref.normal(), next_segment_class)
        elif not real_title and (is_tanakh or is_perek_pasuk_ref):  # not a commentator, but instead a ref to the parsha
            current_source = Source(u"{} {}:{}".format(parser.en_sefer, new_perek, new_pasuk), "bible")
        # elif current_source.parshan_name != "bible":
        #     pass # look for mechilta? look for other books so not to get only Tanakh?
        elif len(relevant_text.split()) < 12:  # not found yet, look it up in library.get_refs_in_string
            found_ref_in_string = self._get_refs_in_string([relevant_text], next_segment_class,
                                                           add_if_not_found=False)
            #todo: I don't love the special casing for Mekhilta here... :(
            if re.search(u"מכילתא", relevant_text) and re.search(u"Exodus(.*)", found_ref_in_string):
                r = u"Mekhilta d'Rabbi Yishmael {}".format(re.search(u"Exodus(.*)", found_ref_in_string).group(1).strip())
                current_source = Source(r, next_segment_class)
            else:
                current_source = Source(found_ref_in_string, next_segment_class)
        else:
            current_source = Source("", next_segment_class)

        # finally set about_source_ref
        if current_source.get_ref():
            if not a_tag_is_entire_comment and found_ref_in_string == "": # and len(relevant_text.split()) >= 6:
                # case where you found the ref but Nechama said something else in addition to the ref
                # so we want to keep the text
                if len(relevant_text.strip(":").split()) <= 1:  # in Ref(current_source.ref).index.all_titles('he'):
                    # print relevant_text.strip(":")
                    pass
                else:
                    current_source.about_source_ref = relevant_text
        elif found_a_tag:
            # found no reference but did find an a_tag so this is a ref so keep the text
            # this test below helps distinguish between "Ibn Caspi" and a long comment
            if len(relevant_text.split()) > len(found_a_tag.text.split()) * 4:
                current_source.about_source_ref = relevant_text
            elif is_perek_pasuk_ref:
                current_source.ref = u"{} {}:{}".format(parser.en_sefer, new_perek, new_pasuk)
            else:
                current_source.ref = relevant_text
            parser.index_not_found[parser.current_file_path].append(current_source.about_source_ref)
        else:
            current_source.about_source_ref = relevant_text

        current_source.parshan_id = 0 if len(next_segment_info)<2 else next_segment_info[1]
        current_source.snunit_ref = snunit_ref
        current_source.about_source_ref = relevant_text
        return current_source

    @staticmethod
    def exctract_pasuk_from_snunit(a_tag):
        book_table = {1: u'Genesis', 2: u'Exodus', 3: u'Leviticus', 4: u'Numbers', 5: u'Deuteronomy',
                      6: u'Joshua',
                      7: u'Judges',
                      11:  u'Jeremiah',
                      12: u'Ezekiel',
                      14: u'Joel',
                      26: u'Psalms',}
            #8: u'I Samuel', 9: u'II Samuel', 10: u'I Kings', 11: u'II Kings', 12: u'Isaiah', 13: u'Jeremiah', 14: u'Ezekiel', 15: u'Hosea', 16: u'Joel', 17: u'Amos', 18: u'Obadiah', 19: u'Jonah', 20: u'Micah', 21: u'Nahum', 22: u'Habakkuk', 23: u'Zephaniah', 24: u'Haggai', 25: u'Zechariah', 26: u'Malachi', 27: u'Psalms', 28: u'Proverbs', 29: u'Job', 30: u'Song of Songs', 31: u'Ruth', 32: u'Lamentations', 33: u'Ecclesiastes', 34: u'Esther', 35: u'Daniel', 36: u'Ezra', 37: u'Nehemiah', 38: u'I Chronicles', 39: u'II Chronicles'}
        match = re.search(u"""kodesh\.snunit\.k12\.il/i/t/t(.{2})(.{2})\.htm#(\d*$)""", a_tag['href'])
        r = None
        if match:
            book_num = match.group(1)
            chapter = match.group(2)
            # a4 = קד בתהילים, e5 קמה
            verse = match.group(3) if match.group(3) else u""
            if int(book_num) not in book_table.keys():
                print u"********* book {}, {} \n {}, {}".format(book_num, a_tag['href'], a_tag.text)
                return None
            if int(book_num) == 26:
                psalms_ch_table = {'0': 0, 'a': 100, 'b': 110, 'c': 120, 'd': 130, 'e': 140, 'f': 150}
                psalms_ch = lambda x: psalms_ch_table[x[0]]+int(x[1])
                chapter = psalms_ch(chapter)
            book = book_table[int(book_num)]
            ref_st = u'{} {} {}'.format(book, chapter, verse).strip()
            r = Ref(ref_st)
            print a_tag['href'], a_tag.text, r.normal()
        return r

    def parse_ref_new(self, segment, relevant_text, next_segment_info): #bad try to put in parshan_id_table to read the parshan from the class number it has
        next_segment_class = next_segment_info[0]
        next_segment_class_id = None if len(next_segment_info)<2 else next_segment_info[1]
        real_title, found_a_tag, a_tag_is_entire_comment, snunit_ref = self.get_a_tag_from_ref(segment, relevant_text)
        found_ref_in_string = ""

        # check if it's in Perek X, Pasuk Y format and set perek and pasuk accordingly
        is_tanakh = (relevant_text.startswith(u"פרק ") or relevant_text.startswith(u"פסוק ") or
                     relevant_text.startswith(u"פרקים ") or relevant_text.startswith(u"פסוקים "))
        is_perek_pasuk_ref, new_perek, new_pasuk = self.set_current_perek_pasuk(relevant_text, next_segment_class,
                                                                                is_tanakh)
        # now create current_source based on real_title or based on self.current_parsha_ref
        if next_segment_class == "parshan":
            try:
                parshan = parser.parshan_id_table[next_segment_class_id]
                assert parshan
                current_source = Source(next_segment_class,
                                        u"{} on {} {}:{}".format(parshan, parser.en_sefer, new_perek, new_pasuk))
                current_source.parshan_name = parshan
            except (KeyError, AssertionError):
                # print "PARSHAN not in table", next_segment_class_id, relevant_text
                if real_title:  # a ref to a commentator that we have in our system
                    if new_pasuk:
                        current_source = Source(u"{} {}:{}".format(real_title, new_perek, new_pasuk), next_segment_class)
        if real_title and not next_segment_class == "parshan":  # a ref to a commentator that we have in our system
            if new_pasuk:
                current_source = Source(u"{} {}:{}".format(real_title, new_perek, new_pasuk), next_segment_class)
            else:
                current_source = Source(u"{} {}".format(real_title, new_perek), next_segment_class)
        elif not real_title and is_tanakh:  # not a commentator, but instead a ref to the parsha
            # if next_segment_class == "parshan":
            #     parshan = parser.parshan_id_table[next_segment_class_id]
            #     print "PARSHAN", parshan, next_segment_class_id
            #     current_source = Source(next_segment_class, u"{} on {} {}:{}".format(parshan, parser.en_sefer, new_perek, new_pasuk))
            #     current_source.parshan_name = parshan
            current_source = Source(u"{} {}:{}".format(parser.en_sefer, new_perek, new_pasuk), "bible")
        elif len(relevant_text.split()) < 8:  # not found yet, look it up in library.get_refs_in_string
            found_ref_in_string = self._get_refs_in_string([relevant_text], next_segment_class,
                                                           add_if_not_found=False)
            current_source = Source(next_segment_class, found_ref_in_string)
        else:
            current_source = Source("", next_segment_class)

        #finally set about_source_ref
        if current_source.get_ref():
            if not a_tag_is_entire_comment and found_ref_in_string == "" and len(relevant_text.split()) >= 6:
                # edge case where you found the ref but Nechama said something else in addition to the ref
                # so we want to keep the text
                current_source.about_source_ref = relevant_text
        elif found_a_tag:
            # found no reference but did find an a_tag so this is a ref so keep the text
            current_source.about_source_ref = relevant_text
            parser.index_not_found[parser.current_file_path].append(current_source.about_source_ref)
        else:
            current_source.about_source_ref = relevant_text

        return current_source

    def _get_refs_in_string(self, strings, next_segment_class, add_if_not_found=True):
        not_found = []
        for string in strings:
            orig = string
            string = "(" + string.replace(u"(", u"").replace(u")", u"") + ")"
            words_to_replace = [u"פרשה", u"*", chr(39), u"פרק", u"פסוק", u"השווה"]
            for word in words_to_replace:
                string = string.replace(u"ל" + word, u"")
                string = string.replace(word, u"")
            string = string.replace(u"  ", u" ").replace(u"\xa0", u" ")
            string = string.strip()
            refs = library.get_refs_in_string(string)
            if refs:
                return refs[0].normal()
            else:
                not_found.append(orig)
        # if len(not_found) == len(strings):
        #     if strings[-1] not in parser.ref_not_found.keys():
        #         parser.ref_not_found[strings[-1]] = 0
        #     parser.ref_not_found[strings[-1]] += 1
        return ""

    def set_current_perek(self, perek, is_tanakh, sefer):
        new_perek = str(getGematria(perek))
        if is_tanakh:
            if new_perek in self.possible_perakim:
                self.current_perek = str(new_perek)
                self.current_parsha_ref = ["bible", u"{} {}".format(sefer, new_perek)]
        return True, new_perek, None
    

    def set_current_pasuk(self, pasuk, is_tanakh):
        pasuk = pasuk.strip()
        if len(pasuk)-1 > pasuk.find("-") > 0:  # is a range, correct it
            start = pasuk.split("-")[0]
            end = pasuk.split("-")[1]
            start = getGematria(start)
            end = getGematria(end)
            new_pasuk = u"{}-{}".format(start, end)
        else:  # there is a pasuk but is not ranged
            new_pasuk = str(getGematria(pasuk))

        if is_tanakh or self.RT_Rashi:
            poss_ref = self.pasuk_in_parsha_pasukim(new_pasuk)
            if poss_ref:
                self.current_perek = poss_ref.sections[0]
                self.current_pasuk = poss_ref.sections[1]# if not poss_ref.is_range() else u"{}-{}".format(poss_ref.sections[1], poss_ref.toSections[1])
            else:

                self.current_parsha_ref = ["bible", u"{} {}".format(parser.en_sefer, self.current_perek)]
        return True, self.current_perek, new_pasuk

    def set_current_perek_pasuk(self, a_tag, text, next_segment_class, is_tanakh=True):
        # text = re.search(u"(פרק(ים))",text)
        text = text if not a_tag else a_tag.text #this is useful for cases when pattern "Perek X Pasuk Y" occurs twice and one is inside a tag
        text = text.replace(u"פרקים", u"Perek").replace(u"פרק ", u"Perek ").replace(u"פסוקים", u"Pasuk").replace(
            u"פסוק ", u"Pasuk ").strip()
        digit = re.compile(u"^.{1,2}[\)|\.]").match(text)
        sefer = parser.en_sefer

        if digit:
            text = text.replace(digit.group(0), "").strip()
        text += " "  # this is hack so that reg ex works

        text = text.replace(u'\u2013', "-").replace(u"\u2011", "-")

        perek_comma_pasuk = re.findall("Perek (.{1,5}), (.{1,9})", text)
        if not perek_comma_pasuk:
            perek_comma_pasuk = re.findall("Perek (.{1,5}),? Pasuk (.{1,9})", text)
        perek = re.findall("Perek (.{1,5}\s)", text)
        pasuk = re.findall("Pasuk (.*?)\s", text) #pasuk = re.findall("Pasuk (.{1,5}(?:-.{1,5})?)", text)

        if len(perek) >= 2 or len(pasuk) >= 2 or len(perek_comma_pasuk) >= 2: #if it's mentioned more than once, it's a comment not a ref
            return False, self.current_perek, self.current_pasuk

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
            pasuk = pasuk.strip()
            new_perek = str(getGematria(perek))
            if len(pasuk)-1 > pasuk.find("-") > 0: # is a range, correct it
                start = pasuk.split("-")[0]
                end = pasuk.split("-")[1]
                start = getGematria(start)
                end = getGematria(end)
                new_pasuk = u"{}-{}".format(start, end)
            else:  # there is a pasuk but is not ranged
                new_pasuk = str(getGematria(pasuk))

            if is_tanakh or self.RT_Rashi:
                poss_ref = self.pasuk_in_parsha_pasukim(new_pasuk, perakim=[new_perek])
                if poss_ref:
                    self.current_perek = poss_ref.sections[0]
                    self.current_pasuk = poss_ref.sections[1] #if not poss_ref.is_range() else u"{}-{}".format(poss_ref.sections[1], poss_ref.toSections[1])
                    # assert str(poss_ref.sections[0]) == new_perek or str(poss_ref.toSections[0]) == new_perek
                    # assert str(poss_ref.sections[1]) == new_pasuk or str(poss_ref.toSections[1]) == new_pasuk
                    self.current_parsha_ref = ["bible", u"{} {}".format(parser.en_sefer, self.current_perek)]
            return True, new_perek, new_pasuk
        return False, self.current_perek, self.current_pasuk


    def relevant_text(self, segment):
        if isinstance(segment, element.Tag):
            # html_tags_and_replacements = [("u", "$!u$", "$/!u$"), ("b", "$!b$", "$/!b$")]
            # for each_tuple in html_tags_and_replacements:
            #     tag, new_start, new_end = each_tuple
            #     for BS_tag in segment.find_all(tag):
            #         new_fake_tag = new_start + segment.text + new_end
            #         BS_tag.replace_with(new_fake_tag)
            return segment.text
        else:
            return segment


    def rt_rashi_out(self, segment):
        classes = parser.important_classes[:] #todo: probbaly should be a list of classes of our Obj somewhere
        classes.extend(["question2", "question", "table"])
        bs_segs = segment.find_all(attrs={"class": classes})
        return bs_segs

    def find_all_p(self, segment):
        # return self.rt_rashi_out(segment)
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

    def pasuk_in_parsha_pasukim(self, new_pasuk, perakim=None):
        if perakim is None:
            perakim = self.possible_perakim
        for perek in perakim:
            for parsha_range in parser.parasha_and_haftarot:
                try:
                    sefer = " ".join(parsha_range.split()[0:-1])
                    possible_ref = Ref("{} ".format(sefer) + perek + ":" + new_pasuk)
                    if self.possible_pasukim.contains(possible_ref):
                        return possible_ref
                except InputError:
                    pass

        return None

    def get_children_with_content(self, segment):
        # determine if the text of segment has content
        children_w_contents = [el for el in segment.contents if is_hebrew(self.relevant_text(el)) or any_english_in_str(self.relevant_text(el))]
        return children_w_contents

    def check_for_blockquote_and_table(self, segments, level=2):
        new_segments = []
        # for i, segment in enumerate(segments):
        #     if segment.name == "blockquote" or (
        #             segment.name == "table" and segment.find_all(atrrs={"class": "RT_RASHI"})):
        #         test = segment
        #         while Section.get_tags(test) == 1:
        #             test = Section.get_tags(test)
        #         new_segments += test
        tables = ["table", "tr"]
        for i, segment in enumerate(segments):
            if isinstance(segment, element.Tag):
                class_ = segment.attrs.get("class", [""])[0]
            else:
                new_segments.append(segment)
                continue
            if segment.name == "blockquote":  # this is really many children so add them to list
                new_segments += self.get_children_with_content(segment)
            elif segment.name == "table" and class_ == "RT_RASHI":
                    new_segments += self.find_all_p(segment)
                    self.RT_Rashi = True
                        # question_in_question = [child for child in segment.descendants if
                        #                   child.name == "table" and child.attrs["class"][0] in ["question", "question2"]]
                        # RT_in_question = [child for child in segment.descendants if
                        #                   child.name == "table" and child.attrs["class"][0] in ["RT", "RTBorder"]]
            else:
                # no significant class and not blockquote or table
                new_segments.append(segment)

        level -= 1
        if level > -1:  # go level deeper unless level isn't > 0
            new_segments = self.check_for_blockquote_and_table(new_segments, level)
        return new_segments

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

    def flatten_our_section(self):
        new_section_list = []
        for isegment, segment in enumerate(self.segment_objects):
            if isinstance(segment, Nested):
                new_section_list.extend(segment.choose())
            elif isinstance(segment, Text):
                new_section_list.append(segment.choose())
            else:
                new_section_list.append(segment)
        return new_section_list


class Nechama_Parser:
    def __init__(self, en_sefer, en_parasha, mode, add_to_title='', catch_errors=False):
        if not os.path.isdir("reports/" + en_parasha): # todo: note! this said parsha instead of en_parasha
            os.mkdir("reports/" + en_parasha)

        self.word_count = 0
        #matches, non_matches, index_not_found, and ref_not_found are all dict with keys being file path and values being list
        #of refs/indexes
        self.matches = {}
        self.non_matches = {}
        self.index_not_found = {}
        self.ref_not_found = {}
        self.to_match = True
        self.sheets_linked_to_sheets = []

        self.add_to_title = add_to_title
        self.catch_errors = catch_errors #crash upon error if False; if True, make report of each error
        self.mode = mode  # fast or accurate
        self.en_sefer = en_sefer
        self.en_parasha = en_parasha
        self._term_cache = {}
        self.important_classes = ["parshan", "midrash", "talmud", "bible", "commentary"]
        self.server = SEFARIA_SERVER
        self.segment_report = UnicodeWriter(open("segment_report.csv", 'a'))
        self.section_report = UnicodeWriter(open("section_report.csv", 'a'))
        now = datetime.datetime.now()
        now = now.strftime("%c")
        self.error_report = open("reports/{}/errors {}".format(en_parasha, now), 'w')
        self.has_parasha = [u"מכילתא"]
        self.term_mapping = {}
        self.parshan_id_table = {}
        self.populate_term_mapping_and_id_table()
        self.levenshtein = WeightedLevenshtein()
        self.missing_index = set()
        self.current_file_path = ""
        self.haftarah_mode = False
        self.parasha_and_haftarot = self.get_parasha_and_haftarot(self.en_parasha)
        self.trying_pm = 0


    def populate_term_mapping_and_id_table(self):
        self.term_mapping = {
            u"הכתב והקבלה": u"HaKtav VeHaKabalah, {}".format(self.en_sefer),
            u"חזקוני": u"Chizkuni, {}".format(self.en_sefer),
            u"""הנצי"ב מוולוז'ין""": u"Haamek Davar on {}".format(self.en_sefer),
            u"אונקלוס": u"Onkelos {}".format(self.en_sefer),
            u"שמואל דוד לוצטו": u"Shadal on {}".format(self.en_sefer),
            u"מורה נבוכים א'": u"Guide for the Perplexed, Part 1",
            u"מורה נבוכים ב'": u"Guide for the Perplexed, Part 2",
            u"מורה נבוכים ג'": u"Guide for the Perplexed, Part 3",
            u"תנחומא": u"Midrash Tanchuma, {}".format(self.en_sefer),
            u"בעל גור אריה": u"Gur Aryeh on {}".format(self.en_sefer),
            u"גור אריה": u"Gur Aryeh on {}".format(self.en_sefer), #todo: how does this mapping work? this name is the prime title
            u"""ראב"ע""": u"Ibn Ezra on {}".format(self.en_sefer),
            u"""וראב"ע:""": u"Ibn Ezra on {}".format(self.en_sefer),
            u"עקדת יצחק": u"Akeidat Yitzchak",
            u"תרגום אונקלוס": u"Onkelos {}".format(self.en_sefer),
            u"""רלב"ג""": u"Ralbag Beur HaMilot on Torah, {}".format(self.en_sefer),
            u"ר' אליהו מזרחי": u"Mizrachi, {}".format(self.en_sefer),
            u"""הרא"ם""": u"Mizrachi, {}".format(self.en_sefer),
            u"""ר' יוסף בכור שור""": u"Bekhor Shor, {}".format(self.en_sefer),
            u"בכור שור": u"Bekhor Shor, {}".format(self.en_sefer),
            u"אברבנאל": u"Abarbanel on Torah, {}".format(self.en_sefer),
            u"""המלבי"ם""": u"Malbim on {}".format(self.en_sefer),
            u"משך חכמה": u"Meshech Hochma, {}".format(self.en_parasha),
            u"רבנו בחיי": u"Rabbeinu Bahya, {}".format(self.en_sefer),
            u"מכילתא": u"Mekhilta d'Rabbi Yishmael",
            u"פרקי דר' אליעזר": u"Pirkei DeRabbi Eliezer", # todo: how to broaden this so it is on פרקי דרבי אליעזר also?
            u"בראשית רבה": u"Bereishit Rabbah", # but maybe this is supposed to be caught via ref catching?
            # u'רב סעדיה גאון': u"Saadia Gaon on {}".format(self.en_sefer) # todo: there is no Saadia Gaon on Genesis how does this term mapping work?
        }
        self.levenshtein = WeightedLevenshtein()
        self.missing_index = set()
        self.parshan_id_table = {
            '3': None,  #u'אבן כספי',
            '4': u"Ibn Ezra on {}".format(self.en_sefer),  # u'''ראב"ע''',
            '6': u"Abarbanel on Torah, {}".format(self.en_sefer),  # Abarbanel_on_Torah,_Genesis
            '8': None,  # אהרליך, מקרא כפשוטו 400.4
            '11': None,  # בעל צידה לדרך 1092.3
            '15': None,  # רבי יוסף אלבו
            '23': None,  #u"רבי אליעזר אשכנזי",
            '24': None,  # הואיל משה 504.2
            '27': None,  #u"בובר"
            '28': u"Rabbeinu Bahya, {}".format(self.en_sefer),  # u'''רבנו בחיי''',
            '29': u"Bekhor Shor, {}".format(self.en_sefer),  # u"בכור שור",
            '32': u"Ralbag on Torah, {}".format(self.en_sefer),
            '33': None,  # u'''ר' אברהם בן הרמב"ם''',
            '37': u"Malbim on {}".format(self.en_sefer),  # u'''מלבי"ם''',
            '38': u"Rashbam on {}".format(self.en_sefer),  # רשב"ם
            '39': u'Ramban on {}'.format(self.en_sefer),  # u'''רמב"ן''',
            '41': u'Or HaChaim on {}'.format(self.en_sefer),  # Or_HaChaim_on_Genesis
            '43': None,  # u'''בעל ספר הזיכרון''',
            '46': u"Haamek Davar on {}".format(self.en_sefer),
            '51': None,  # u"ביאור - ר' שלמה דובנא"
            '53': None,  # רב דוד הופמן
            '59': None,  # ר' וולף היידנהיים 176.9
            '64': None,  # u'רש"ר הירש'
            '66': u"Meshech Hochma, {}".format(self.en_parasha),
            '73': None,  # ר' נפתלי הירץ ויזל
            '78': u"Chizkuni, {}".format(self.en_sefer),  # u'החזקוני'
            '88': None,  # u'אברהם כהנא (פירוש מדעי)'
            '91': u"Gur Aryeh on {}".format(self.en_sefer),  # u"גור אריה",
            '94': u"Shadal on {}".format(self.en_sefer),  # u'''שד"ל''',
            '101': u'Mizrachi, {}'.format(self.en_sefer),
            '104': None,  # u'''רמבמ"ן''',
            '107': None,  # u'רס"ג'
            '109': u'Sforno on {}'.format(self.en_sefer),
            '111': u"Akeidat Yitzchak",  # u'''עקדת יצחק''',
            '118': None,  # u'קסוטו',
            '127': u"Radak on {}".format(self.en_sefer),  # u'''רד"ק''',
            '152': None,  # u'בנו יעקב',
            '157': None, #  volz
            '158': None,  # רוזנצוויג
            '161': None,  # הרמב"ם דוגמא 4 ב
            '162': u"Rashi on {}".format(self.en_sefer),
            '170': None,  # באור
            '175': None,  # u"כור הזהב",
            '177': u'',  #השגות הראב"ד
            '178': u"Sefer HaChinukh",
            '179': None,  # שם עולם 176.6
            '183': None,  #
            '187': None,  # ר' יוסף נחמיאש
            '196': None,  # u'''בעל הלבוש אורה''',
            '198': u"HaKtav VeHaKabalah, {}".format(self.en_sefer),  # u'''הכתב והקבלה''',
            '238': u"Onkelos {}".format(self.en_sefer),  # u"אונקלוס",
        # u'''רלב"ג''', #todo, figure out how to do Beur HaMilot and reguler, maybe needs to be a re.search in the changed_ref method
        }
        for k in range(239):
            if str(k) not in self.parshan_id_table.keys():
                self.parshan_id_table[str(k)] = None


    def flip_ref_parasha_to_haftarah(self, ref, haftarah):
        haftarah_index = Ref(haftarah).index.title
        try:
            base_ref = ref.split(" on ")[1] if " on " in ref else ref #strip "Rashi on Genesis 2" to "Genesis 2"
            orig_index = library.get_index(" ".join(base_ref.split()[0:-1])) # now strip "Genesis 2" to "Genesis"
        except BookNameError:
            return ref
        orig_index = orig_index.title
        ref = ref.replace(orig_index, haftarah_index)
        return ref

    def source_maybe_tanakh(self, ref):
        try:
            i = library.get_index(" ".join(ref.split()[0:-1]))
        except BookNameError:
            book_name = " ".join(ref.split()[0:-1])
            book_name = book_name.split(" on ")[-1]
            try:
                i = library.get_index(book_name)
            except BookNameError:
                return True # returning True because at this stage we have things like "Meshech Hochma, Ki Teitzei"
                            # and "Onkelos Leviticus" and there's no clear test for these cases even though they are Tanakh
        return i.categories[0] == "Tanakh"


    def get_parasha_and_haftarot(self, parasha_to_find):
        parshiot = list(db.parshiot.find({"parasha": parasha_to_find}))
        if parshiot:
            return parshiot[0]["haftara"]["ashkenazi"]+[parshiot[0]["ref"]] #["ashkenazi"]
        return []

    def download_sheets(self):
        parshat_bereshit = ["1", "2", "30", "62", "84", "148", "212", "274", "302", "378", "451", "488", "527",
                            "563", "570", "581", "750", "787", "820", "844", "894", "929", "1021", "1034", "1125",
                            "1183", "1229", "1291", "1351", "1420"]
        start_after = 35
        for i in range(1500):
            if i <= start_after or str(i) in parshat_bereshit:
                continue
            sleep(3)
            headers = {
                'User-Agent': 'Mozilla/4.0 (Macintosh; Intel Mac OS X 11_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
            response = requests.get("http://www.nechama.org.il/pages/{}.html".format(i), headers=headers)
            if response.status_code == 200:
                with open("{}.html".format(i), 'w') as f:
                    f.write(response.content)
            else:
                print "No page at {}.html".format(i)

    def dict_from_html_attrs(self, contents):
        d = OrderedDict()
        for e in [e for e in contents if isinstance(e, element.Tag)]:
            if "id" in e.attrs.keys():
                d[e.attrs['id']] = e
            else:
                d[e.name] = e
        return d

    def get_score(self, words_a, words_b):

        str_a = u" ".join(words_a)
        str_b = u" ".join(words_b)
        dist = self.levenshtein.calculate(str_a, str_b, normalize=True)

        return dist

    def clean(self, s):
        s = unicodedata.normalize("NFD", s)
        s = strip_cantillation(s, strip_vowels=True)
        s = re.sub(u"(^|\s)(?:\u05d4['\u05f3])($|\s)", u" יהוה ", s)
        s = re.sub(ur"[,'\":?.!;־״׳-]", u" ", s)
        s = re.sub(u'((?:^|\s)[\u05d0-\u05ea])\s+([\u05d0-\u05ea])', ur"\1\2", s)
        # s = re.sub(ur"-", u"", s)
        s = re.sub(u'''(^|\s)דה\s''', u" ", s)
        if not re.search(u'^\([^()]*(?:\)\s*)$', s):
            s = re.sub(ur"\([^)]+\)", u" ", s)
        # s = re.sub(ur"\([^)]+\)", u" ", s)
        # s = re.sub(ur"\((?:\d{1,3}|[\u05d0-\u05ea]{1,3})\)", u" ", s)  # sefaria automatically adds pasuk markers. remove them
        s = bleach.clean(s, strip=True, tags=()).strip()
        s = u" ".join(s.split())
        return s

    def tokenizer(self, s):
        return self.clean(s).split()


    def check_reduce_sources(self, comment, ref):
        new_ref = []
        # rashbam on 821
        if isinstance(ref.text('he').text, list) and all([isinstance(x, list) for x in ref.text('he').text]) and any([isinstance(x, int) for deep1 in ref.text('he').text for x in deep1]):
            print "OOF"
            return new_ref
        n = len(comment.split())
        if n<=5:
            ngram_size = n
            max_words_between = 1
            min_words_in_match = n-2
        else:
            ngram_size = 3
            max_words_between = 4
            min_words_in_match = int(round(n*0.3))

        pm = ParallelMatcher(self.tokenizer, dh_extract_method=None, ngram_size=ngram_size, max_words_between=max_words_between, min_words_in_match=min_words_in_match,
        min_distance_between_matches=0, all_to_all=False, parallelize=False, verbose=False, calculate_score=self.get_score)
        if self.to_match:
            new_ref = pm.match(tc_list=[ref.text('he'), (comment, 1)], return_obj=True)
            new_ref = [x for x in new_ref if x.score > 80]
        return new_ref

    def change_ref_to_commentary(self, ref, comment_ind):
        ls = LinkSet(ref)
        commentators_on_ref = [x.refs[0] if x.refs[0] != ref.normal() else x.refs[1] for x in ls if Ref(x.refs[0]).is_commentary() or Ref(x.refs[1]).is_commentary()]
        for comm in commentators_on_ref:
            if comment_ind in Ref(comm).index.title:
                return Ref(comm).section_ref()
        if self.en_sefer in comment_ind:
            comment_ind = re.search(u'(.*?) on (?:.*?){}'.format(self.en_sefer), comment_ind).group(1)
            for comm in commentators_on_ref:
                if comment_ind in Ref(comm).index.title:
                    return Ref(comm).section_ref()
        return ref

    def try_parallel_matcher(self, current_source, guess_ref = None, guess_parshan = None):
        # if isinstance(current_source.ref, Ref):
        #     current_source.ref = current_source.ref.normal()
        try:
            try:
                if not current_source.get_sefaria_ref(current_source.ref):
                    if guess_ref:
                        if re.search(u" on ", current_source.ref):
                            commentator = re.split(u" on ", current_source.ref)[0]
                            ref2check = current_source.get_sefaria_ref(u"{} on {}".format(commentator, re.split(u" on ", current_source.ref)[1] if re.search(u" on ", guess_ref) else guess_ref))
                        else:
                            ref2check = current_source.get_sefaria_ref(guess_ref)
                    else:
                        ref2check = None
                else:
                    ref2check = current_source.get_sefaria_ref(current_source.ref)
            except InputError:
                if u"Meshech Hochma" in current_source.ref:
                    ref2check = Ref(u"Meshech Hochma, {}".format(self.en_parasha))
            text_to_use = u""
            if self.mode == "fast":
                text_to_use = u" ".join(current_source.text.split()[0:15])
            elif self.mode == "accurate":
                text_to_use =u" ".join(current_source.text) if isinstance(current_source.text, list)  else current_source.text
            # todo: one Source obj for different Sefaria refs. how do we deal with this?
            if ref2check:
                text_to_use = self.clean(text_to_use)  # .replace('"', '').replace("'", "")
                if len(text_to_use.split()) <= 1:
                    if isinstance(ref2check.text('he').text[0], list): #2d list
                        tc = strip_cantillation(" ".join(numpy.concatenate(ref2check.text('he').text)))
                    else: # either string or 1d list
                        tc = ref2check.text('he').text if not isinstance(ref2check.text('he').text, list) else strip_cantillation(" ".join(ref2check.text('he').text))
                    if strip_cantillation(text_to_use, strip_vowels=True) in strip_cantillation(tc, strip_vowels=True).split():
                        current_source.ref = ref2check.normal()
                        return True
                        # print current_source.ref
                    else:
                        # print "it is one or less words and this is the wrong ref..."
                        return False
                else:
                    matched = self.check_reduce_sources(text_to_use, ref2check) # returns a list ordered by scores of mesorat hashas objs that were found
                    changed_ref = ref2check  # ref2chcek might get a better ref but also might not...
                    # if not matched:  # no match found  - parshan id try
                    if current_source.parshan_id or guess_parshan:
                        try:
                            if not current_source.parshan_id:
                                current_source.parshan_id = guess_parshan
                            parshan = parser.parshan_id_table[current_source.parshan_id]
                            # chenged_ref = Ref(u'{} {}'.format(parshan, u'{}:{}'.format(ref2check.sections[0], ref2check.sections[1]) if len(ref2check.sections)>1 else u'{}'.format(ref2check[0])))
                            assert parshan
                            changed_ref = self.change_ref_to_commentary(ref2check, parshan)
                            if changed_ref !=ref2check:
                                matched1 = self.check_reduce_sources(text_to_use, changed_ref)
                                matched = matched if len(matched)>=len(matched1) else matched1
                        except KeyError:
                            print u"parshan_id_table is missing a key and value for {}, in {}, \n text {}".format(current_source.parshan_id, self.current_file_path, current_source.text)
                        except AssertionError as e:
                            print e
                            pass
                        except: # this is here because this small try shouldn't fly all the way to the try of all the PM and not use what it might have found. i know it is not good practice
                            pass
                    # look one level up - todo: is checking level up duplicated?
                    if not matched:  # and parshan is a running parshan, still not matched! מלבים. אברבנל.העמק דבר רלבג
                        matched = self.check_reduce_sources(text_to_use, changed_ref.top_section_ref())
                    # check Haftarah
                    if not matched and current_source.ref and parser.source_maybe_tanakh(
                            current_source.ref) and parser.haftarah_mode:
                        for opt in parser.parasha_and_haftarot:
                            changed_ref = self.flip_ref_parasha_to_haftarah(current_source.ref, opt)
                            if current_source.ref == changed_ref:
                                continue
                            current_source.ref = changed_ref
                            self.trying_pm += 1
                            if self.trying_pm < 2:
                                pm_output = self.try_parallel_matcher(current_source, current_source.guess_ref)
                                matched = pm_output[1] if not isinstance(pm_output, bool) else []
                            else:
                                self.trying_pm = 0
                                return False

                    if not matched:  # still not matched...
                        # print u"NO MATCH : {}".format(text_to_use)
                        self.non_matches[self.current_file_path].append(ref2check.normal())

                        # we dont want to link it since there's no match found so set the ref to empty.
                        # current_source.about_source_ref = ref2check.he_normal() # record the fixed ref ref2check in about_source_ref (not sure why this was a good idea...)
                        current_source.ref = ""
                        return False
                    else:
                        self.matches[self.current_file_path].append(ref2check.normal())
                        current_source.ref = matched[0].a.ref.normal() if matched[0].a.ref.normal() != 'Berakhot 58a' else matched[
                            0].b.ref.normal()  # because the sides change

                        # if ref2check.is_section_level():
                            # print '** section level ref: '.format(ref2check.normal())
                        return True, matched
            else:
                # print u"NO ref2check {}".format(current_source.parshan_name)
                if current_source.ref:
                    parser.ref_not_found[parser.current_file_path].append(current_source.ref)
                return False
        except AttributeError as e:
            parser.index_not_found[parser.current_file_path].append(current_source.about_source_ref)  # todo: would like to add just the <a> tag
            return False
        except IndexError as e:
            parser.index_not_found[parser.current_file_path].append(ref2check.normal())
            return False



    def organize_by_parsha(self, file_list_names):
        """
        The main BeautifulSoup reader function, that etrates on all sheets and creates the obj, probably should be in it's own file
        :param self:
        :return:
        """
        sheets = OrderedDict()
        for html_sheet in file_list_names:
            content = BeautifulSoup(open("{}".format(html_sheet)), "lxml")
            top_dict = dict_from_html_attrs(content.find('div', {'id': "contentTop"}).contents)
            parsha = top_dict["paging"].text
            shutil.move(html_sheet, "html_sheets/" + parsha)
        return sheets

    def bs4_reader(self, file_list_names, post = False, add_to_title = ""):
        """
        The main BeautifulSoup reader function, that etrates on all sheets and creates the obj, probably should be in it's own file
        :param self:
        :return:
        """
        sheets = OrderedDict()
        for html_sheet in file_list_names:
            try:
                parser.current_file_path = html_sheet
                parser.matches[parser.current_file_path] = []
                parser.non_matches[parser.current_file_path] = []
                parser.index_not_found[parser.current_file_path] = []
                parser.ref_not_found[parser.current_file_path] = []
                with open("{}".format(html_sheet)) as f:
                    file_content = f.read()
                    file_content = file_content.replace("<U>", "<B>").replace("</U>", "</B>").replace("<u>", "<b>").replace("</u>", "</b>")
                content = BeautifulSoup(file_content, "lxml")
                parser.haftarah_mode = u"הפטרה" in content.text or u"הפטרת" in content.text
                # if not parser.haftarah_mode:
                #     continue
                print "\n\n"
                print datetime.datetime.now()
                print html_sheet
                perek_info = content.find("p", {"id": "pasuk"}).text

                top_dict = dict_from_html_attrs(content.find('div', {'id': "contentTop"}).contents)
                # print 'len_content type ', len(top_dict.keys())
                sheet = Sheet(html_sheet, top_dict["paging"].text, top_dict["h1"].text, top_dict["year"].text, perek_info)
                sheet.links_to_other_sheets = bool(content.find_all("a", {"href": re.compile("^http.*?nechama.org.il/pages/")}))
                sheets[html_sheet] = sheet
                body_dict = dict_from_html_attrs(content.find('div', {'id': "contentBody"}))
                sheet.div_sections.extend([v for k, v in body_dict.items() if re.search(u'ContentSection_\d', k)]) # check that these come in in the right order
                sheet.sheet_remark = body_dict['sheetRemark'].text
                # sheet.sheet_remark = str(body_dict['sheetRemark'])
                # sheet.sheet_remark = bleach.clean(sheet.sheet_remark, tags=["a"], strip=True)
                sheet.parse_as_text()
                sheet.create_sheetsources_from_objsource()
                sheet.prepare_sheet(add_to_title, post=post)
            except Exception, e:
                if parser.catch_errors:
                    self.error_report.write(html_sheet+": ")
                    self.error_report.write(str(sys.exc_info()[0:2]))
                    self.error_report.write("\n")
                    self.error_report.write(traceback.format_exc())
                    self.error_report.write("\n\n")
                else:
                    raise
        return sheets

    def record_report(self):
        if not self.catch_errors:
            return

        now = datetime.datetime.now()
        now = now.strftime("%c")
        if not os.path.isdir("reports/{}".format(self.en_parasha)):
            os.mkdir("reports/{}".format(self.en_parasha))
        new_file = codecs.open("reports/{}/{} {}.txt".format(self.en_parasha, self.add_to_title, now), 'w', encoding='utf-8')
        parasha_matches = parasha_non_matches = parasha_total = parasha_ref_not_found = parasha_index_not_found = 0
        metadata_tuples = [(self.non_matches, "Non-matches", parasha_non_matches),
                           (self.ref_not_found, "Refs not found", parasha_ref_not_found),
                           (self.index_not_found, "Indexes not found", parasha_index_not_found)]
        for curr_file_path in self.matches.keys():
            sheet_matches = sheet_non_matches = sheet_total = 0.1
            new_file.write("\n\n"+curr_file_path)

            sources = self.matches[curr_file_path]
            if sources:
                new_file.write("\n{} - {}\n".format("Matches", len(sources)))
                new_file.write(u", ".join(sources))
                sheet_matches += len(sources)

            for tuple in metadata_tuples:
                metadata_dict, title, count = tuple
                sources = metadata_dict[curr_file_path]
                if sources:
                    new_file.write("\n{} - {}\n".format(title, len(sources)))
                    new_file.write(u", ".join(sources))
                    sheet_non_matches += len(sources)
                    count += len(sources)


            sheet_total = sheet_matches + sheet_non_matches
            if sheet_total: #something it's 0, why? Noach/5.html
                percent = 100.0*float(sheet_matches)/sheet_total
                new_file.write("\nSheet Total: {}".format(sheet_total))
                new_file.write("\nSheet Matches: {}".format(sheet_matches))
                new_file.write("\nSheet Percent Matched: {0:.2f}%".format(percent))
                parasha_matches += sheet_matches
                parasha_total += sheet_total
                parasha_non_matches += sheet_non_matches

        if not parasha_total:
            parasha_total = 0.01

        percent = 100.0*float(parasha_matches)/parasha_total
        new_file.write("\n\n\nParasha Total: {}".format(parasha_total))
        new_file.write("\nParasha Matches: {}".format(parasha_matches))
        new_file.write("\nParasha Percent Matched: {0:.2f}%".format(percent))

        new_file.close()


    def prepare_term_mapping(self):
        i = library.get_index("Midrash Tanchuma")
        node = i.nodes.children[2]
        node.add_title("Genesis", 'en')
        i.save()
        i = library.get_index("Gur Aryeh on Bereishit")
        i.nodes.add_title("Gur Aryeh on Genesis", 'en')
        i.save()
        i = library.get_index("Gur Aryeh on Bamidbar")
        i.nodes.add_title("Gur Aryeh on Numbers", 'en')
        i.save()
        i = library.get_index("Gur Aryeh on Devarim")
        i.nodes.add_title("Gur Aryeh on Deuteronomy", 'en')
        i.save()
        i = library.get_index("Meshech Hochma")
        node = library.get_index("Meshech Hochma").nodes.children[4]
        node.add_title("Chayei Sara", 'en')
        node = library.get_index("Meshech Hochma").nodes.children[6]
        node.add_title("Vayetzei", "en")
        node = library.get_index("Meshech Hochma").nodes.children[45]
        node.add_title("Korach", "en")
        i.save()
        t = Term().load({"titles.text": "Ki Tisa"})
        t.add_title(u'פרשת כי-תשא', 'he')
        t.save()
        t = Term().load({'titles.text': "Bechukotai"})
        t.add_title(u'פרשת בחקותי', 'he')
        t.save()
        t = Term().load({"titles.text": "Sh'lach"})
        t.add_title(u'פרשת שלח לך', 'he')
        t.save()
        t = Term().load({"titles.text": "Pinchas"})
        t.add_title(u'פרשת פינחס', 'he')
        t.save()


def dict_from_html_attrs(contents):
    d = OrderedDict()
    for e in [e for e in contents if isinstance(e, element.Tag)]: #for e in [e for e in contents if isinstance(e, element.Tag)]:
        if "id" in e.attrs.keys():
            d[e.attrs['id']] = e
        else:
            d[e.name] = e
    return d
#
# def word_cloud():
#     def get_title(el):
#         index = Ref(el).index
#         collective_title = getattr(index, "collective_title", None)
#         if collective_title:
#             term = Term().load({"name": collective_title}).get_titles('he')[0].encode('utf-8')
#         else:
#             term = index.get_title('he').split(u" על ")[0].encode('utf-8')
#         term = term.replace(" ", "־").replace('"', '״')
#         return term
#
#     from collections import Counter
# from sefaria.system.database import db
# sheets = db.sheets.find()
# sheets = list(sheets)
# wordsByYear = {}
# for sheet in sheets:
#     year = sheet["summary"].split(" ")[0]
#     if year not in wordsByYear:
#         wordsByYear[year] = 0
#     sources = sheet["sources"]
#     text = ""
#     for source in sources:
#         print source
#         if "text" in source.keys():
#             text += source["text"]["he"]
#         elif "outsideText" in source.keys():
#             text += source["outsideText"]
#         else:
#             continue
#     num_words = len(text.split())
#     wordsByYear[year] += num_words


    # includedRefs = Counter()
    # includedRefsTotal = Counter()
    # includedCommentary = Counter()
    # includedIndexes = Counter()
    # includedTanakh = Counter()
    # refsPerSheet = Counter()
    # total = 0
    # for sheet in sheets:
    #     total += len(sheet["includedRefs"])
    #     refsPerSheet[sheet["id"]] = len(sheet["includedRefs"])
    #     includedRefs[sheet["title"]] = Counter(sheet["includedRefs"])
    #     includedTanakh += Counter([Ref(el).index for el in sheet["includedRefs"]
    #                                if "Commentary" not in Ref(el).index.categories and "Tanakh" in Ref(el).index.categories])
    #     includedIndexes += Counter([Ref(el).index for el in sheet["includedRefs"] if "Commentary" not in Ref(el).index.categories and "Tanakh" not in Ref(el).index.categories])
    #     includedCommentary += Counter([Ref(el).index for el in sheet["includedRefs"] if "Commentary" in Ref(el).index.categories])
    #     includedRefsTotal += includedRefs[sheet["title"]]




if __name__ == "__main__":
    # Ref(u"בראשית פרק ג פסוק ד - פרק ה פסוק י")
    # Ref(u"u'דברים פרק ט, ז-כט - פרק י, א-י'")

    

    genesis_parshiot = (u"Genesis", ["Bereshit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", 'Vayetzei',
                                     "Vayishlach", "Vayeshev", "Miketz", "Vayigash", "Vayechi"])
    exodus_parshiot = (u"Exodus", ["Vayakhel-Pekudei", "Shemot", "Vaera", "Bo", "Beshalach", "Yitro", "Mishpatim",
                                   "Terumah", "Tetzaveh", "Vayakhel", "Ki Tisa", "Pekudei"])
    leviticus_parshiot = (u"Leviticus", ["Vayikra", "Tzav", "Shmini", "Tazria", "Metzora", "Tazria-Metzora", "Achrei Mot",
                        "Kedoshim", "Achrei Mot-Kedoshim", "Emor", "Behar", "Bechukotai", "Behar-Bechukotai"])
    numbers_parshiot = (u"Numbers", ["Matot-Masei", "Bamidbar", "Nasso", "Beha'alotcha", "Sh'lach", "Korach", "Chukat",
                        "Balak", "Pinchas", "Matot", "Masei"])
    devarim_parshiot = (u"Deuteronomy", ["Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo",
                        "Nitzavim", "Vayeilech", "Nitzavim-Vayeilech", "Ha'Azinu", "V'Zot HaBerachah"])
    catch_errors = False
    posting = True
    individual = 1


    for which_parshiot in [genesis_parshiot, devarim_parshiot]: #genesis_parshiot ,exodus_parshiot,leviticus_parshiot,numbers_parshiot,devarim_parshiot
        print "NEW BOOK"
        for parsha in which_parshiot[1]:
            book = which_parshiot[0]
            parser = Nechama_Parser(book, parsha, "accurate", "he_ref", catch_errors=catch_errors) #accurate
            parser.prepare_term_mapping()  # must be run once locally and on sandbox
            #parser.bs4_reader(["html_sheets/Bereshit/787.html"], post=False)
            if not individual:
                sheets = [sheet for sheet in os.listdir("html_sheets/{}".format(parsha)) if sheet.endswith(".html")]
                # anything_before = "7.html"
                # pos_anything_before = sheets.index(anything_before)
                # sheets = sheets[pos_anything_before:]
                # sheets = sheets[sheets.index("163.html")::]
            if individual:
                got_sheet = parser.bs4_reader(["html_all/{}.html".format(individual)] if "{}.html".format(individual) in os.listdir("html_sheets/{}".format(parsha)) else [], post=posting)
            else:
                sheets = parser.bs4_reader(["html_sheets/{}/{}".format(parsha, sheet) for sheet in sheets if sheet in os.listdir("html_sheets/{}".format(parsha)) and sheet != "163.html"], post=posting)
            if catch_errors:
                parser.record_report()
            if individual and got_sheet:
              break
        if individual and got_sheet:
            break
    print 'Done'
    # print word_count
    # with open("sheets_linked_to_sheets.csv", 'w') as f:
    #     writer = UnicodeWriter(f)
    #     writer.writerows(sheets_linked_to_sheets)


