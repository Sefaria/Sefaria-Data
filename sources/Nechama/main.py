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
# from fuzzywuzzy import fuzz
import datetime
import traceback
import unicodecsv as csv


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
        if self.sheet_remark.strip():
            parser.word_count += len(self.sheet_remark)
            self.sources.append({"outsideText": self.sheet_remark,
             "options": {
                 "indented": "indented-1",
                 "sourceLayout": "",
                 "sourceLangLayout": ""

             }
             })
        for isection, section in enumerate(self.sections):
            self.sources.extend(self.create_sheetsources_from_sections(section.segment_objects)) # vs section and than getting the section.segment_objects latter in create_sheetsources_from_sections function



    def create_sheetsources_from_sections(self, segment_objects):
        sheets_sources = []
        guess_ref = u""
        guess_parshan = '162'
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
                            guess_parshan_name = Ref(segment.ref).index.title
                            guess_parshan_opt = filter(lambda x: x[1]==guess_parshan_name, parser.parshan_id_table.items())
                            if guess_parshan_opt:
                                guess_parshan = filter(lambda x: x[1] == guess_parshan_name, parser.parshan_id_table.items())[0][0]

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
                        segment.segment_objs[0].number = q_source.number
                        segment.segment_objs[0].difficulty = q_source.difficulty
                        # q_source.q_text = segment.segment_objs[0].ref
                        # segment.segment_objs[0].ref = q_source.format()
                        #
                        # q_source.q_text = segment.segment_objs[0].about_source_ref
                        # segment.segment_objs[0].about_source_ref = q_source.format()
                    else:
                        try:
                            q_source.q_text = segment.segment_objs[0].text if hasattr(segment.segment_objs[0], 'text') else segment.segment_objs[0].sp_segment.text
                        except AttributeError:
                            q_source.q_text = segment.segment_objs[0].segment_objs[0].text if hasattr(segment.segment_objs[0].segment_objs[0],'text') else segment.segment_objs[0].segment_objs[0].sp_segment.text

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

    @staticmethod
    def he_letter_to_en_leter(letter):
        letter = getGematria(letter)
        if letter > 26:
            return u""  # probably not a number like 91.2 Buber
        return chr(letter + 96)

    def prepare_sheet(self, add_to_title="", post=False):
       sheet_json = {}
       sheet_json["status"] = "public" #"private" #
       sheet_json["group"] =u"גיליונות נחמה" #"Nechama Leibowitz' Source Sheets"
       # sheet_json["title"] = u'{} - {} {}'.format(self.title, re.search('(\d+)\.', self.html).group(1), add_to_title)
       sheet_json["title"] = u"{} {} - {}".format(self.parasha, self.he_year, self.title)
       sheet_json["summary"] = u"{} ({})".format(self.en_year, self.he_year)
       # sheet_json["attribution"] = u"<a href=http://www.nechama.org.il/pages/{}.html>לגליון זה באתר סנונית</a>".format(re.search('(\d+)\.', self.html).group(1))
       sheet_json["sources"] = self.sources
       sheet_lang = 'bilingual' if parser.english_sheet else 'hebrew'
       sheet_json["options"] = {"numbered": 0, "assignable": 0, "layout": "sideBySide", "boxed": 0, "language": sheet_lang, "divineNames": "noSub", "collaboration": "group-can-edit", "highlightMode": 0, "bsd": 0, "langLayout": "heRight"}

       if "-" in self.en_parasha:
           sheet_json["tags"] = [unicode(self.en_parasha.split("-")[0]), unicode(self.en_parasha.split("-")[-1])]
           # sheet_json['tags'].extend([unicode(self.parasha.split(u"-")[0]), u"פרשת {}".format(unicode(self.parasha.split(u"-")[-1]))])
           assert Term().load({"name": self.en_parasha.split("-")[0]})
           assert Term().load({"name": self.en_parasha.split("-")[-1]})
       else:
           sheet_json["tags"] = [unicode(self.en_parasha)]
           # sheet_json['tags'].append(self.parasha)
           assert Term().load({"name": self.en_parasha})
       sheet_json["tags"].append(re.search(u'.*?(\d+)\.', self.html).groups(1)[0])
       # sheet_json["tags"].append()
       if parser.english_sheet:
           sheet_json['tags'].append(u'Bilingual')
       else:
           sheet_json['tags'].append(u'Hebrew Sheet')
       if self.links_to_other_sheets:
           # sheet_json['tags'].append('Sheet2Sheet')
           parser.sheets_linked_to_sheets.append((sheet_json["title"], sheet_json["summary"], sheet_json["tags"]))
       talmud = library.get_indexes_in_category('Talmud')
       for i, s in enumerate(sheet_json['sources']):
           compile = re.compile(u'<sup class="nechama">(?P<difficulty>.*?)</sup>\s*(?P<number>.{1,2}\.)?')
           if 'outsideText' in s.keys():
               if 'class="nechama"' in s['outsideText']:
                   match = re.search(compile, s['outsideText'])
                   if match:
                        sub_with = u''
                        if match.group("number"):
                            sub_with = u'{}'.format(match.group("number"))
                        s['outsideText'] = re.sub(compile, sub_with, s['outsideText'])
                        s["options"] = dict()
                        s['options']['sourcePrefix'] = match.group(1)
           else: # Text sheet object look for the numbering issue.
                try:
                    Ref(s['heRef'])
                except (InputError, KeyError):
                    match = re.search(u'(?P<number>.{1,2})\.\s*(?P<extract_ref>.*$)', s['heRef'])
                    if match:
                        ref = match.group("extract_ref").strip()
                        try:
                            ref = re.split(u'-', ref)[0]  # looks like the Ref(ref) doesn't know how to deal with ranges...
                            assert Ref(ref)
                        except (AssertionError, InputError):
                            if Ref(s['ref']).book not in talmud:
                                print "this ref {} is problematic. it is in node {}".format(ref, i)
                        s['heRef'] = ref
                        # s['ref'] = Ref(ref).normal()
                        s['options']['PrependRefWithHe'] = u'{}. '.format(match.group("number"))
                        if parser.english_sheet:
                            en_number = match.group("number") if match.group("number").isdigit() else u'{}'.format(Sheet.he_letter_to_en_leter(match.group("number")))
                            s['options']['PrependRefWithEn'] = u'{}. '.format(en_number)


           for sheet_link in parser.ssn_dicts:
               if 'outsideText' in s.keys():
                   uni_outsidetext = unicode(s['outsideText'], encoding='utf8') if isinstance(s['outsideText'], str) else s['outsideText']
                   if re.search(sheet_link[u'text'], uni_outsidetext, flags=re.IGNORECASE):
                       s['outsideText'] = re.sub(sheet_link[u'text'], sheet_link[u'linked_text'],  uni_outsidetext, flags=re.IGNORECASE)

           if snunit_links:
               for snunit_dict in parser.snunit_outside_texts:
                   if len(snunit_dict[u'words'])<=1:
                       continue
                   source_type = None
                   if 'outsideText' in s.keys():
                       uni_outsidetext = unicode(s['outsideText'], encoding='utf8') if isinstance(s['outsideText'],str) else s['outsideText']
                       source_type = 'outsideText'
                   elif 'text' in s.keys():
                       uni_outsidetext = unicode(s['text']['he'], encoding='utf8') if isinstance(s['text']['he'],str) else s['text']['he']
                       source_type = 'text'
                   else:
                       continue

                   if re.search(u"""{}""".format(snunit_dict[u'words']).replace(u')', u'').replace(u'(', u''), uni_outsidetext):
                       new_ref = u'''<a href="/{}" target="_blank" class="refLink">{}</a>'''.replace(u'(', u'').replace(u')', u'').format(snunit_dict['ref'].normal(), snunit_dict[u'words'])
                       linked_text = re.sub(snunit_dict[u'words'].replace(u')', u'').replace(u'(', u''), new_ref, uni_outsidetext)
                       self.test_snunit_links(link_text = snunit_dict[u'words'], link_ref = snunit_dict['ref'])
                       if source_type == 'outsideText':
                           s['outsideText'] = linked_text
                       elif source_type == 'text':
                           s['text']['he'] = linked_text
       if post:
           if parser.english_sheet:
               for i, s in enumerate(sheet_json['sources']):
                   if 'outsideText' in s.keys():
                       s['outsideBiText'] = dict()
                       s['outsideBiText']['he'] = s['outsideText']
                       s['outsideBiText']['en'] = "translation here"
                       # get headers in English to look like headers in hebrew
                       if re.match(u'.*?<table><tr><td><big>', s['outsideBiText']['he']):
                           match = re.match('(.*>)[^<]+(<.*)', s['outsideBiText']['he'])
                           s['outsideBiText']['en'] = '{}translation here{}'.format(match.group(1), match.group(2))
                       elif re.match(u".*?<span style='color:rgb\(153,153,153\);'>", s['outsideBiText']['he']):
                           s['outsideBiText']['en'] = "<span style='color:rgb(153,153,153);'>source name</span><br/><span style='color:rgb(51,51,51);'>source translation"
                       elif 'options' in s.keys() and 'sourcePrefix' in s['options'].keys(): #re.match(u'.*?<sup class="nechama">\*{0,2}</sup>', s['outsideBiText']['he']):
                           matches = re.match(u'(^.{1,2})\.', s['outsideBiText']['he'])
                           # diffculty = matches.group(1)
                           # number = u""
                           if matches and matches.group(1):
                               number = matches.group(1)[0] if matches.group(1)[0].isdigit() else u'{}'.format(Sheet.he_letter_to_en_leter(matches.group(1)[0]))
                               s['outsideBiText']['en'] = u'{}. question here'.format(number)
                       # for sheet_link in parser.ssn_dicts:
                       #      uni_outsidetext = unicode(s['outsideBiText']['he'], encoding='utf8') if isinstance(s['outsideBiText']['he'],str) else s['outsideBiText']['he']
                       #      if re.search(sheet_link[u'text'], uni_outsidetext):
                       #          s['outsideBiText']['he'] = re.sub(sheet_link[u'text'], sheet_link[u'linked_text'], uni_outsidetext)

                       del s['outsideText']
                   else:  # Text
                       s['options']['sourceLanguage'] = ""
                       q_numbering = re.search(u'(.*\.)', s['heRef'])
                       if re.search(u'(^.{1,2}\.)', s['heRef']):
                           print q_numbering.group(1)
                           s['enRef'] = u'{} {}'.format(q_numbering.group(1), s['ref'])
                       if not s['text']['en']:
                            s['text']['en'] = "segment translation"
               self.test_no_lists(sheet_json['sources'])


           # sheet_json['id'] = int([x for x in sheet_json['tags'] if x.isdigit()][0])-1477
           # #look liike we need to dealete the one that is there. the right thing to do ius to take this as an approtunity to use post sheet correctly.
           # #so create it as a post at the end of the list and pull it over.
           response = post_sheet(sheet_json, server=parser.server)
           if not isinstance(response, dict):
               with open(u"nopost.html", 'a') as f:
                   writer = f.write(response)

    def test_no_lists(self, sources):
        for s in sources:
            if 'outsideBiText' in s.keys():
                assert not isinstance(s['outsideBiText']['he'], list)
                assert not isinstance(s['outsideBiText']['en'], list)
            else:
                assert not isinstance(s['text']['he'], list)
                assert not isinstance(s['text']['en'], list)

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

    def test_snunit_links(self, link_text, link_ref):
        link_text = library.get_refs_in_string(u'({})'.format(link_text))
        if link_ref not in link_text:
            print u"link_text {}, link_ref {}".format(link_text, link_ref)

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
        soup_segments = self.check_for_blockquote_and_table(soup_segments)
        for segment in soup_segments:
            class_ = ""
            if isinstance(segment, element.Tag):
                class_ = segment.attrs.get("class", [""])[0]
            if segment.name == "table" and class_ == "RT_RASHI":
                self.RT_Rashi = True
        # blockquote is really just its children so get replace it with them
        # and tables  need to be handled recursively

        # create Segment objects out of the BeautifulSoup objects
        self.classify_segments(soup_segments)  # self.segment_objects += self.classify_segments(soup_segments)
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
            nested_seg = Nested.is_nested(sp_segment, just_checking=True)  # Question.nested(sp_segment)
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
                # else:
                #     return Nechama_Comment(relevant_text)

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
            real_title = parser.parshan_id_table.get(parshan_id, 0)
            if real_title==0:
                with codecs.open(u'reports/parshan_id_table.txt', 'a', encoding='utf-8') as fp:
                    fp.write(u"{}\n".format(self.number))
                    fp.write(u"{}:{}\n".format(parshan_id, a_tag.text))
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
                      81: u'I Samuel',
                      82: u'II Samuel',
                      91: u'I Kings',
                      92: u'II Kings',
                      10: u'Isaiah',
                      11: u'Jeremiah',
                      12: u'Ezekiel',
                      13: u'Hosea', 14: u'Joel', 15: u'Amos', 16: u'Obadiah', 17: u'Jonah', 18: u'Micah', 19: u'Nahum',
                      20: u'Habakkuk', 21: u'Zephaniah', 22: u'Haggai', 23: u'Zechariah', 24: u'Malachi',
                      251: u'I Chronicles',
                      252: u'II Chronicles',
                      26: u'Psalms',
                      27: u'Job',
                      28: u'Proverbs',
                      29: u'Ruth', 30: u'Song of Songs', 32: u'Lamentations', 31: u'Ecclesiastes', 33: u'Esther',
                      34: u'Daniel',
                      351: u'Ezra',
                      352: u'Nehemiah'
                      }
        if isinstance(a_tag,basestring):
            match = re.search(u"""kodesh\.snunit\.k12\.il/i/tr?/t(?P<book>\d\d)(?P<onetwo>.?)(?P<ch>.\d)\.htm#?((?P<verse>\d+?)")?""", a_tag)
        else:
            match = re.search(u"""kodesh\.snunit\.k12\.il/i/tr?/t(?P<book>\d\d)(?P<onetwo>.?)(?P<ch>.\d)\.htm#?(?P<verse>\d*$)?""", a_tag['href'])
        r = None
        if match:
            book_num = match.group('book')
            chapter = match.group('ch')
            # a4 = קד בתהילים, e5 קמה
            onetwo = match.group('onetwo')
            verse = match.group('verse')

            if int(book_num) == 26 and not chapter[0].isdigit():
                psalms_ch_table = {'a': 100, 'b': 110, 'c': 120, 'd': 130, 'e': 140, 'f': 150}
                psalms_ch = lambda x: psalms_ch_table[x[0]]+int(x[1])
                chapter = psalms_ch(chapter)
            if onetwo:
                onetwo= 1 if onetwo == 'a' else 2
                book_num = int('{}{}'.format(book_num, onetwo))
            try:
                book = book_table[int(book_num)]
            except KeyError:
                book = 'no book'
                print "Book number error {}".format(book_num)
            ref_st = u'{} {} {}'.format(book, chapter, verse).replace('None', '').strip()
            try:
                r = Ref(ref_st)
                if isinstance(a_tag, basestring):
                    print a_tag, r.normal()
                else:
                    print a_tag['href'], a_tag.text, r.normal()
            except InputError as e:
                if isinstance(a_tag, basestring):
                    print a_tag
                else:
                    print a_tag['href'], a_tag.text, e
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
            # elif segment.name == "table" and class_ == "RT_RASHI":
            #         new_segments += self.find_all_p(segment)
            #         self.RT_Rashi = True
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
    def __init__(self, en_sefer, en_parasha, mode, add_to_title=u'', catch_errors=False, looking_for_matches=True, english_sheet=False):
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
        self.english_sheet = english_sheet
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
        self.looking_for_matches = looking_for_matches
        #use self.create_map_ssn_url() to create the specific map that is needed
        self.map_ssn_url = {}
        # self.map_ssn_url = {
        # 1: 153241, 2: 151103, 3: 151180, 4: 151181, 5: 151182, 6: 151183, 7: 151184, 8: 151185, 9: 151186, 10: 151187,
        # 11: 151188, 12: 151189, 13: 151190, 14: 151191, 15: 151192, 16: 151193, 17: 151194, 19: 151196, 20: 151197,
        # 21: 151198, 22: 151199, 23: 151200, 24: 151201, 25: 151202, 26: 151203, 27: 152663, 28: 151205, 29: 151206,
        # 30: 151207, 31: 151208, 32: 151209, 33: 151210, 34: 151211, 35: 153228, 36: 153216, 37: 151214, 38: 151215,
        # 39: 151216, 40: 151217, 41: 151218, 42: 151219, 43: 151220, 44: 151221, 45: 151222, 46: 151223, 47: 151224,
        # 48: 151225, 49: 151226, 50: 151227, 51: 153190, 52: 151229, 53: 151230, 54: 151231, 55: 151232, 56: 151233,
        # 57: 151234, 58: 151235, 59: 151236, 60: 152148, 61: 151238, 62: 153152, 63: 151240, 64: 151241, 65: 151242,
        # 67: 151243, 68: 151244, 70: 151245, 71: 151246, 72: 151247, 73: 151248, 74: 151249, 75: 151250, 76: 151251,
        # 77: 151252, 78: 151253, 79: 151254, 80: 151255, 81: 151256, 82: 151257, 83: 151258, 84: 151259, 85: 151260,
        # 86: 151261, 87: 151262, 88: 151263, 89: 151264, 90: 151265, 91: 151266, 92: 151267, 93: 151268, 94: 151269,
        # 95: 151270, 96: 151271, 97: 151272, 98: 151273, 99: 151274, 100: 151275, 101: 153191, 102: 151277, 103: 152682,
        # 104: 151279, 105: 151280, 106: 151281, 107: 151282, 108: 151283, 109: 151284, 110: 151285, 111: 151286,
        # 112: 151287, 113: 151288, 114: 152661, 115: 152662, 116: 151291, 117: 151292, 118: 153229, 119: 153217,
        # 120: 151295, 121: 151296, 122: 151297, 123: 151298, 124: 151299, 125: 151300, 126: 151301, 127: 151302,
        # 128: 151303, 129: 151304, 130: 151305, 131: 151306, 132: 151307, 133: 151308, 134: 151309, 135: 151310,
        # 136: 151311, 137: 151312, 138: 151313, 139: 151314, 140: 151315, 141: 151316, 142: 151317, 143: 151318,
        # 144: 151319, 145: 151320, 146: 151321, 147: 151322, 148: 151323, 149: 151324, 150: 151325, 151: 153192,
        # 152: 151327, 153: 151328, 154: 151329, 155: 151330, 156: 151331, 157: 151332, 158: 151333, 159: 151334,
        # 160: 151335, 161: 151336, 162: 151337, 164: 151338, 165: 151339, 166: 151340, 167: 151341, 168: 151342,
        # 169: 153230, 170: 153218, 171: 151345, 172: 151346, 173: 151347, 174: 151348, 175: 151349, 176: 151350,
        # 177: 151351, 178: 151352, 179: 151353, 180: 151354, 181: 151355, 182: 151356, 183: 151357, 184: 151358,
        # 185: 151359, 186: 151360, 187: 151361, 188: 151362, 189: 151363, 190: 151364, 191: 151365, 192: 151366,
        # 193: 151367, 194: 151368, 195: 151369, 196: 151370, 197: 151371, 198: 151372, 199: 151373, 200: 151374,
        # 201: 153193, 202: 153155, 203: 151377, 204: 151378, 206: 151379, 207: 151380, 208: 151381, 209: 151382,
        # 210: 151383, 211: 151384, 212: 151385, 213: 151386, 214: 151387, 215: 151388, 216: 151389, 217: 151390,
        # 218: 151391, 219: 151392, 220: 151393, 221: 151394, 222: 151395, 223: 151396, 224: 151397, 225: 151398,
        # 226: 151399, 227: 153242, 228: 151401, 229: 151402, 230: 151403, 231: 151404, 232: 151405, 233: 151406,
        # 234: 151407, 235: 151408, 236: 151409, 237: 151410, 238: 151411, 239: 151412, 240: 151413, 241: 151414,
        # 242: 151415, 243: 151416, 244: 151417, 245: 151418, 246: 151419, 247: 151420, 248: 151421, 249: 151422,
        # 250: 151423, 251: 153194, 252: 151425, 253: 151426, 254: 151427, 255: 151428, 256: 151429, 257: 151430,
        # 258: 151431, 259: 153231, 260: 153219, 261: 151434, 262: 151435, 263: 151436, 264: 151437, 265: 151438,
        # 266: 151439, 267: 151440, 268: 151441, 269: 151442, 270: 151443, 271: 151444, 272: 151445, 273: 151446,
        # 274: 151447, 275: 151448, 276: 151449, 277: 151450, 278: 151746, 279: 151452, 280: 151453, 281: 151454,
        # 282: 151455, 283: 151456, 284: 151457, 285: 151458, 286: 151459, 287: 151460, 288: 151461, 289: 151462,
        # 290: 151463, 291: 151464, 292: 151465, 293: 151466, 294: 151467, 295: 151468, 296: 151469, 297: 151470,
        # 298: 151471, 299: 151472, 300: 151473, 301: 153195, 302: 153156, 303: 151476, 304: 151477, 305: 151478,
        # 306: 151479, 307: 151480, 308: 151481, 309: 151482, 310: 151483, 311: 151484, 312: 151485, 313: 151486,
        # 314: 151487, 315: 151488, 316: 151489, 317: 151490, 318: 151491, 319: 151492, 320: 151493, 321: 151494,
        # 322: 151495, 323: 151496, 324: 151497, 325: 151498, 326: 151499, 327: 151500, 328: 151501, 329: 151502,
        # 330: 151503, 331: 151504, 332: 151505, 333: 151506, 334: 151507, 335: 153243, 336: 151509, 337: 151510,
        # 338: 151511, 339: 151512, 340: 151513, 341: 151514, 342: 151515, 343: 151516, 344: 151517, 345: 151518,
        # 346: 151519, 347: 151520, 348: 151521, 349: 151522, 350: 151523, 351: 153196, 352: 151525, 353: 151526,
        # 354: 151527, 355: 153244, 356: 151529, 357: 151530, 358: 151531, 359: 151532, 360: 151533, 361: 151534,
        # 362: 151535, 363: 151536, 364: 151537, 365: 151538, 366: 151539, 367: 151540, 368: 151541, 369: 151542,
        # 370: 151543, 371: 151544, 372: 151545, 373: 151546, 374: 151547, 375: 151548, 376: 151549, 377: 151550,
        # 378: 151551, 379: 151552, 380: 151553, 381: 151554, 382: 151555, 383: 151556, 384: 151557, 385: 151558,
        # 386: 151559, 387: 151560, 388: 151561, 389: 151562, 390: 151563, 391: 151564, 392: 151565, 393: 151566,
        # 394: 151567, 395: 151568, 396: 151569, 397: 151570, 398: 151571, 399: 151572, 400: 151573, 401: 153197,
        # 402: 151575, 403: 151576, 404: 151577, 405: 151578, 406: 151579, 407: 151580, 408: 151581, 409: 151582,
        # 410: 151583, 411: 151584, 412: 151585, 413: 151586, 414: 151587, 415: 151588, 416: 151589, 417: 151590,
        # 418: 151591, 419: 151592, 420: 151593, 421: 151594, 422: 151595, 423: 151596, 424: 151597, 425: 151598,
        # 426: 151599, 427: 151600, 428: 151601, 429: 151602, 430: 151603, 431: 151604, 432: 151605, 433: 151606,
        # 434: 151607, 435: 151608, 436: 151609, 437: 151610, 438: 151611, 439: 151612, 440: 151613, 441: 151614,
        # 442: 151615, 443: 151616, 444: 151617, 445: 151618, 446: 151619, 447: 151620, 448: 151621, 449: 151622,
        # 450: 151623, 451: 153198, 452: 151625, 453: 151626, 454: 151627, 455: 151628, 456: 151629, 457: 151630,
        # 458: 151631, 459: 151632, 460: 151633, 461: 151634, 462: 151635, 463: 151636, 464: 151637, 465: 151638,
        # 466: 151639, 467: 151640, 468: 151641, 469: 151642, 470: 151643, 471: 151644, 472: 151645, 473: 151646,
        # 474: 151647, 475: 151648, 476: 151649, 477: 151650, 478: 151651, 479: 151652, 480: 151653, 481: 151654,
        # 482: 151655, 483: 151656, 484: 151657, 485: 151658, 486: 151659, 487: 151660, 488: 151661, 489: 151662,
        # 490: 151663, 491: 151664, 492: 151665, 493: 151666, 494: 151667, 495: 151668, 496: 151669, 497: 151670,
        # 498: 151671, 499: 151672, 500: 151673, 501: 153199, 502: 152690, 503: 152683, 504: 151677, 505: 151678,
        # 506: 151679, 507: 151680, 508: 151681, 509: 151682, 510: 151683, 511: 151684, 512: 151685, 513: 151686,
        # 514: 151687, 515: 151688, 516: 151689, 517: 151690, 518: 151691, 519: 151692, 520: 151693, 521: 151694,
        # 522: 151695, 523: 151696, 524: 151697, 525: 151698, 526: 151699, 527: 151700, 528: 151701, 529: 151702,
        # 530: 151703, 531: 151704, 532: 151705, 533: 151706, 534: 151707, 535: 151708, 536: 151709, 537: 151710,
        # 538: 151711, 539: 151712, 540: 151713, 541: 151714, 542: 151715, 543: 151716, 544: 151717, 545: 151718,
        # 546: 151719, 547: 151720, 548: 151721, 549: 151722, 550: 151723, 551: 153200, 552: 151725, 553: 151726,
        # 554: 151727, 555: 151729, 556: 151730, 557: 151731, 558: 151732, 559: 151733, 560: 151734, 561: 151735,
        # 562: 151737, 563: 151738, 564: 151739, 565: 151740, 566: 151741, 567: 151742, 568: 151743, 569: 151744,
        # 570: 151745, 571: 151747, 572: 151748, 573: 151749, 574: 151750, 575: 151751, 576: 151752, 577: 151753,
        # 579: 151754, 580: 151755, 581: 151756, 582: 151757, 583: 151758, 584: 151759, 585: 151760, 586: 151761,
        # 587: 151762, 588: 151763, 589: 151764, 590: 151765, 591: 151766, 592: 151767, 593: 151768, 594: 151769,
        # 595: 151770, 596: 151771, 597: 151772, 598: 151773, 599: 151774, 600: 151775, 601: 153201, 602: 152671,
        # 603: 152684, 604: 151779, 605: 151780, 606: 151781, 607: 151782, 608: 151783, 609: 153246, 610: 151785,
        # 611: 151786, 612: 151787, 613: 151788, 614: 151789, 615: 151790, 616: 151791, 617: 151792, 618: 151793,
        # 619: 153232, 620: 153220, 621: 151796, 622: 151797, 623: 151798, 624: 151799, 625: 151800, 626: 151801,
        # 628: 151802, 629: 151803, 630: 151804, 631: 151805, 632: 151806, 633: 151807, 634: 151808, 635: 151809,
        # 636: 151810, 637: 151811, 638: 151812, 639: 151813, 640: 151814, 641: 151815, 642: 151816, 643: 151817,
        # 644: 151818, 645: 151819, 646: 151820, 647: 151821, 648: 151822, 649: 151823, 650: 151824, 651: 153202,
        # 652: 151826, 653: 151827, 654: 151828, 655: 151829, 656: 151830, 657: 151831, 658: 151832, 659: 151833,
        # 660: 151834, 661: 152657, 662: 151836, 663: 151837, 664: 151838, 665: 151839, 666: 151840, 667: 151841,
        # 668: 151842, 670: 151844, 671: 151845, 672: 151846, 673: 151847, 674: 151848, 675: 151849, 676: 151850,
        # 677: 151851, 678: 151852, 679: 153249, 680: 151854, 681: 151855, 682: 151856, 683: 151857, 684: 151858,
        # 685: 151859, 686: 151860, 687: 151861, 688: 151862, 689: 151863, 690: 151864, 691: 151865, 692: 151866,
        # 693: 151867, 694: 151868, 695: 151869, 696: 151870, 697: 151871, 698: 151872, 699: 151873, 700: 151874,
        # 701: 153203, 702: 151876, 703: 152685, 704: 151878, 705: 151879, 706: 151880, 707: 151881, 708: 151882,
        # 709: 151883, 710: 151884, 711: 151885, 712: 151886, 713: 151887, 714: 151888, 715: 151889, 716: 151890,
        # 717: 151891, 718: 151345, 719: 151893, 720: 151894, 721: 151895, 722: 151896, 723: 151897, 724: 151898,
        # 725: 151899, 726: 151900, 727: 151901, 728: 151902, 729: 151903, 730: 151904, 731: 151905, 732: 151906,
        # 733: 151907, 734: 151908, 735: 151909, 736: 151910, 737: 151911, 738: 151912, 739: 151913, 740: 151914,
        # 741: 151915, 742: 151916, 743: 151917, 744: 151918, 745: 151919, 746: 151920, 747: 151921, 748: 151922,
        # 749: 151923, 750: 151924, 751: 153204, 752: 151926, 753: 151927, 754: 151928, 755: 151929, 756: 151930,
        # 757: 151931, 758: 151932, 759: 151933, 760: 151934, 761: 151935, 762: 151936, 763: 151937, 764: 151938,
        # 765: 151939, 766: 151940, 767: 151941, 768: 151942, 769: 151943, 770: 151944, 771: 151945, 772: 151946,
        # 773: 151947, 774: 153233, 775: 153221, 776: 151950, 777: 151951, 778: 151952, 779: 151953, 780: 151954,
        # 781: 151955, 782: 151956, 783: 151957, 784: 151958, 785: 151959, 786: 151960, 787: 151961, 788: 151962,
        # 789: 151963, 790: 151964, 791: 151965, 792: 151966, 793: 151967, 794: 151968, 795: 151969, 796: 151970,
        # 797: 151971, 798: 151972, 799: 151973, 800: 151974, 801: 153205, 802: 152672, 803: 152686, 804: 151978,
        # 805: 151979, 806: 151980, 807: 151981, 808: 151982, 809: 151983, 810: 151984, 811: 151985, 812: 151986,
        # 813: 151987, 814: 151988, 815: 151989, 816: 151990, 817: 151991, 818: 151992, 819: 151993, 820: 151994,
        # 821: 151995, 822: 151996, 823: 151997, 824: 151998, 825: 151999, 826: 152000, 827: 152001, 828: 152002,
        # 829: 152003, 830: 152004, 831: 152005, 832: 152006, 833: 152007, 834: 152008, 835: 152009, 836: 152010,
        # 837: 152011, 838: 152012, 839: 152013, 840: 152014, 841: 152015, 842: 152016, 843: 152017, 844: 152018,
        # 845: 152019, 846: 152020, 847: 152021, 848: 152022, 849: 152023, 850: 152024, 851: 153206, 852: 152026,
        # 853: 152027, 854: 152028, 855: 152029, 856: 152030, 857: 152031, 858: 152032, 859: 152033, 860: 152034,
        # 861: 152035, 862: 152036, 863: 152037, 864: 152038, 865: 152039, 866: 152040, 867: 152041, 868: 152042,
        # 869: 152043, 870: 152044, 871: 152045, 872: 152046, 873: 152047, 874: 152048, 875: 152049, 876: 152050,
        # 877: 152051, 878: 152052, 879: 152053, 880: 152054, 881: 152055, 882: 152056, 883: 152057, 884: 152058,
        # 885: 152059, 886: 152060, 887: 152061, 888: 152062, 889: 152063, 890: 152064, 891: 152065, 892: 152066,
        # 893: 152067, 894: 152068, 895: 152069, 896: 152070, 897: 152071, 898: 152072, 899: 152073, 900: 152074,
        # 901: 153207, 902: 152680, 903: 152687, 904: 152078, 905: 152079, 906: 152080, 907: 152081, 908: 152082,
        # 909: 152083, 910: 152084, 911: 152085, 912: 152086, 913: 152087, 914: 152088, 915: 152089, 916: 152090,
        # 917: 152091, 918: 152092, 919: 152093, 920: 152094, 921: 152095, 922: 152096, 923: 152097, 924: 152098,
        # 925: 152099, 926: 152100, 927: 152101, 928: 152102, 929: 152103, 930: 152104, 931: 152105, 932: 152106,
        # 933: 152107, 934: 152108, 935: 152109, 936: 152110, 937: 152111, 938: 152112, 939: 152113, 940: 152114,
        # 941: 152115, 942: 152116, 943: 152117, 944: 152118, 945: 152119, 946: 152120, 947: 152121, 948: 152122,
        # 949: 152123, 950: 152124, 951: 153208, 952: 152126, 953: 152127, 954: 152128, 955: 152129, 956: 152149,
        # 957: 152150, 958: 152151, 959: 152152, 960: 152153, 961: 152154, 962: 152155, 963: 152156, 964: 152157,
        # 965: 152158, 966: 152159, 967: 152160, 968: 152161, 969: 152162, 970: 152163, 971: 152164, 972: 152165,
        # 973: 152166, 974: 152167, 975: 152168, 976: 152169, 977: 152170, 978: 152171, 979: 152172, 980: 152173,
        # 981: 152174, 982: 152175, 983: 152176, 984: 152177, 985: 152178, 986: 152179, 988: 152180, 989: 152181,
        # 990: 152182, 991: 152183, 992: 152184, 993: 152185, 994: 152186, 995: 152187, 996: 152188, 997: 152189,
        # 998: 152190, 999: 152191, 1000: 152192, 1001: 153209, 1002: 152674, 1003: 152195, 1004: 152196, 1005: 152197,
        # 1006: 152198, 1007: 152199, 1008: 152200, 1009: 152201, 1010: 152202, 1011: 152203, 1012: 152204, 1013: 152205,
        # 1014: 152206, 1015: 152207, 1016: 152208, 1017: 152209, 1018: 152210, 1019: 152211, 1020: 152212, 1021: 152213,
        # 1022: 152214, 1023: 152215, 1024: 152216, 1025: 152217, 1026: 152218, 1027: 152219, 1028: 152220, 1029: 152221,
        # 1030: 152222, 1031: 152223, 1032: 151182, 1033: 152225, 1034: 152226, 1035: 152227, 1036: 152228, 1037: 152229,
        # 1038: 152230, 1039: 152231, 1040: 152232, 1041: 152233, 1042: 152234, 1043: 152235, 1044: 152236, 1045: 152237,
        # 1046: 152238, 1047: 152239, 1048: 152240, 1049: 152241, 1050: 152242, 1051: 153210, 1052: 152244, 1053: 152245,
        # 1054: 152246, 1055: 152247, 1056: 152248, 1057: 152249, 1058: 152250, 1059: 152251, 1060: 152252, 1061: 152253,
        # 1062: 152254, 1063: 152255, 1064: 152256, 1065: 152257, 1066: 152258, 1067: 152259, 1068: 152260, 1069: 152261,
        # 1070: 152262, 1071: 152263, 1072: 152264, 1073: 152265, 1074: 152266, 1075: 151178, 1076: 152267, 1077: 152268,
        # 1078: 152269, 1079: 152270, 1080: 152271, 1081: 152272, 1082: 152273, 1083: 152274, 1084: 152275, 1085: 152276,
        # 1086: 152277, 1087: 152278, 1088: 152279, 1089: 152280, 1090: 152281, 1091: 152282, 1092: 152283, 1093: 152284,
        # 1094: 152285, 1095: 152286, 1096: 152287, 1097: 152288, 1098: 152289, 1099: 152290, 1100: 152291, 1101: 153211,
        # 1102: 152293, 1103: 152294, 1104: 152295, 1105: 152296, 1106: 152297, 1107: 152298, 1108: 152299, 1109: 152300,
        # 1110: 152301, 1111: 152302, 1112: 152303, 1113: 152304, 1114: 152305, 1115: 152306, 1116: 152307, 1117: 152308,
        # 1118: 152309, 1119: 152310, 1120: 152311, 1121: 152312, 1122: 152313, 1123: 152314, 1124: 152315, 1125: 152316,
        # 1126: 152317, 1127: 152318, 1128: 152319, 1129: 152320, 1130: 152321, 1131: 152322, 1132: 152323, 1133: 152324,
        # 1134: 152325, 1135: 152326, 1136: 152327, 1137: 152328, 1138: 152329, 1139: 152330, 1140: 152331, 1141: 152332,
        # 1142: 152333, 1143: 152334, 1144: 151347, 1145: 152336, 1146: 152337, 1147: 152338, 1148: 152339, 1149: 152340,
        # 1150: 152341, 1151: 153212, 1152: 152343, 1153: 152344, 1154: 152345, 1155: 152346, 1156: 152347, 1157: 152348,
        # 1158: 152349, 1159: 152350, 1160: 152351, 1161: 152352, 1162: 152353, 1163: 151180, 1164: 152354, 1165: 152355,
        # 1166: 152356, 1167: 152357, 1168: 152358, 1169: 152359, 1170: 152360, 1171: 152361, 1172: 152362, 1173: 152363,
        # 1174: 152364, 1175: 152365, 1176: 152366, 1177: 152367, 1178: 152368, 1179: 152369, 1180: 152370, 1181: 152371,
        # 1182: 152372, 1183: 152373, 1184: 152374, 1185: 152375, 1186: 152376, 1187: 152377, 1188: 152378, 1189: 152379,
        # 1190: 152380, 1191: 152381, 1192: 152382, 1193: 152383, 1194: 152384, 1195: 152385, 1196: 152386, 1197: 152387,
        # 1198: 152388, 1199: 152389, 1200: 152390, 1201: 153213, 1202: 152392, 1203: 152393, 1204: 152394, 1205: 152395,
        # 1206: 152396, 1207: 152397, 1208: 152398, 1209: 152399, 1210: 152400, 1211: 152401, 1212: 152402, 1213: 152403,
        # 1214: 152404, 1215: 152405, 1216: 152406, 1217: 152407, 1218: 152408, 1219: 152409, 1220: 152410, 1221: 152411,
        # 1222: 152412, 1223: 152413, 1224: 152414, 1225: 152415, 1226: 152416, 1227: 152417, 1228: 152418, 1229: 152419,
        # 1230: 152420, 1231: 152421, 1232: 152422, 1233: 152423, 1234: 152424, 1235: 152425, 1236: 152426, 1237: 152427,
        # 1238: 152428, 1239: 152429, 1240: 152430, 1241: 152431, 1243: 152432, 1244: 152433, 1245: 152434, 1246: 152435,
        # 1247: 152436, 1248: 152437, 1249: 152438, 1250: 152439, 1251: 153214, 1252: 152441, 1253: 152442, 1254: 152443,
        # 1255: 152444, 1256: 152445, 1257: 152446, 1258: 152447, 1259: 152448, 1260: 152449, 1261: 152450, 1262: 152451,
        # 1263: 152452, 1264: 152453, 1265: 152454, 1266: 152455, 1267: 152456, 1268: 152457, 1269: 152458, 1270: 152459,
        # 1271: 152460, 1272: 152461, 1273: 152462, 1274: 152463, 1275: 152464, 1276: 152465, 1277: 152466, 1278: 152467,
        # 1279: 152468, 1280: 152469, 1281: 152470, 1282: 152471, 1283: 152472, 1284: 152473, 1285: 152474, 1286: 152475,
        # 1287: 152476, 1288: 152477, 1289: 152478, 1290: 152479, 1291: 152480, 1292: 152481, 1293: 152482, 1294: 152483,
        # 1295: 152484, 1296: 152485, 1297: 152486, 1298: 152487, 1299: 152488, 1300: 152489, 1301: 153215, 1302: 152491,
        # 1303: 152492, 1304: 152493, 1305: 152494, 1306: 152495, 1307: 152496, 1308: 152497, 1309: 152498, 1310: 152499,
        # 1311: 152500, 1312: 152501, 1313: 152502, 1314: 152503, 1315: 152504, 1316: 152505, 1317: 152506, 1318: 152507,
        # 1319: 152508, 1320: 151179, 1321: 152509, 1322: 152510, 1323: 152511, 1324: 152512, 1325: 152513, 1326: 152514,
        # 1327: 152515, 1328: 152516, 1329: 152517, 1330: 152518, 1331: 152519, 1332: 152520, 1333: 152521, 1334: 152522,
        # 1335: 152523, 1336: 152524, 1337: 152525, 1338: 152526, 1339: 152527, 1340: 152528, 1341: 152529, 1342: 152530,
        # 1343: 152531, 1344: 152532, 1345: 152533, 1346: 152534, 1348: 152535, 1349: 152536, 1350: 152537, 1351: 153184,
        # 1352: 152539, 1353: 152540, 1354: 152541, 1355: 152542, 1356: 152543, 1357: 152544, 1358: 152545, 1359: 152546,
        # 1360: 152547, 1361: 152548, 1362: 152549, 1363: 152550, 1364: 152551, 1365: 152552, 1366: 152553, 1367: 152554,
        # 1368: 152555, 1369: 152556, 1370: 152557, 1371: 152558, 1372: 152559, 1373: 152560, 1374: 152561, 1375: 152562,
        # 1376: 152563, 1377: 152564, 1378: 152565, 1379: 152566, 1380: 152567, 1381: 152568, 1382: 152569, 1383: 152570,
        # 1384: 152571, 1385: 152572, 1386: 152573, 1387: 152574, 1388: 152575, 1389: 152576, 1390: 152577, 1391: 152578,
        # 1392: 152579, 1393: 152580, 1394: 152581, 1395: 152582, 1396: 152583, 1397: 152584, 1398: 152585, 1399: 152586,
        # 1400: 152587, 1401: 153185, 1402: 153234, 1403: 153235, 1404: 153236, 1405: 153237, 1406: 153238, 1407: 153239,
        # 1408: 153227, 1409: 152596, 1410: 152597, 1411: 152598, 1412: 152599, 1413: 152600, 1414: 152601, 1415: 152602,
        # 1416: 152603, 1417: 152604, 1418: 152605, 1419: 152606, 1420: 152607, 1421: 152608, 1422: 152609, 1423: 152610,
        # 1424: 152611, 1425: 152612, 1426: 152613, 1427: 152614, 1428: 152615, 1429: 152616, 1430: 152617, 1431: 152618,
        # 1432: 152619, 1433: 152620, 1434: 152621, 1435: 152622, 1436: 152623, 1437: 152624, 1438: 152625, 1439: 152626,
        # 1440: 152660, 1441: 152628, 1442: 152629, 1443: 152630, 1444: 152631, 1445: 152632, 1446: 152633, 1447: 152634,
        # 1448: 152635, 1449: 152636, 1450: 152637, 1451: 153186, 1452: 152639, 1455: 152640, 1456: 152641, 1457: 152642,
        # 1458: 152643, 1459: 152644, 1461: 152645, 1464: 152646, 1465: 152647, 1466: 152648, 1467: 152649, 1468: 152650,
        # 1469: 152651, 1472: 152652, 1473: 152653, 1474: 152654, 1478: 152655}
        self.ssn_dicts = []
        self.snunit_outside_texts = []

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
            '9': u'Penei David, {}, {}'.format(self.en_sefer, self.en_parasha),  # פני דוד
            '11': None,  # בעל צידה לדרך 1092.3
            '12': None,  # המהרז"ו 125.2
            '14': u'Mechir Yayin on Esther',  # מחיר יין
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
            '54': None,  # הכורם- ר' הרץ נפתלי הומברג 160.3
            '59': None,  # ר' וולף היידנהיים 176.9
            '60': None,  # ר' אליעזר היילפרין, בפירושו לרש"י באורי מוהרא"ל 2.6
            '63': None,  # פרופ' היינמן 164.1
            '64': None,  # u'רש"ר הירש'
            '66': u"Meshech Hochma, {}".format(self.en_parasha),
            '67': None,  # בעל דברי דוד 125.5
            '73': None,  # ר' נפתלי הירץ ויזל
            '77': u'Rabbeinu Chananel on {}'.format(self.en_sefer),  # רבינו חננאל
            '78': u"Chizkuni, {}".format(self.en_sefer),  # u'החזקוני'
            '85': u'Kitzur Baal Haturim on {}'.format(self.en_sefer),  # קיצור בעל הטורים
            '88': None,  # u'אברהם כהנא (פירוש מדעי)'
            '91': u"Gur Aryeh on {}".format(self.en_sefer),  # u"גור אריה",
            '92': u"Kli Yakar on {}".format(self.en_sefer),  # כלי יקר
            '94': u"Shadal on {}".format(self.en_sefer),  # u'''228.4 שד"ל''',
            '101': u'Mizrachi, {}'.format(self.en_sefer),
            '104': None,  # u'''רמבמ"ן''',
            '107': None,  # u'רס"ג'
            '109': u'Sforno on {}'.format(self.en_sefer),
            '110': u'Bartenura on Torah, {}'.format(self.en_sefer),  #ברטנורא על התורה
            '111': u"Akeidat Yitzchak, {}",  # u'''עקדת יצחק''',
            '112': None,  # משכיל לדוד 71.2
            '118': None,  # u'קסוטו',
            '127': u"Radak on {}".format(self.en_sefer),  # u'''רד"ק''',
            '129': None,  #  ר' יעקב קניזל 85.2
            '145': None,  # בעל מנחת יהודה, 85.3
            '152': None,  # u'בנו יעקב',
            '157': None, #  volz
            '158': None,  # רוזנצוויג
            '161': None,  # הרמב"ם דוגמא 4 ב
            '162': u"Rashi on {}".format(self.en_sefer),
            '168': u'Tzror HaMor on Torah, {}'.format(self.en_sefer),  # צרור המור
            '170': None,  # באור
            '175': None,  # u"כור הזהב",
            '174': u'Torah Temimah on Torah, {}'.format(self.en_sefer),
            '177': u'',  #השגות הראב"ד
            '178': u"Sefer HaChinukh",
            '179': None,  # שם עולם 176.6
            '183': None,  #
            '187': None,  # ר' יוסף נחמיאש
            '188': u'Minchat Shai on Torah, {}'.format(self.en_sefer),  # מנחת שי
            '196': None,  # u'''202.1 בעל הלבוש אורה''',
            '197': u'Alshich on Torah, {}'.format(self.en_sefer),  #האלשיך
            '198': u"HaKtav VeHaKabalah, {}".format(self.en_sefer),  # u'''הכתב והקבלה''',
            '209': None,  #פירוש יפה תואר 85.1
            '238': u"Onkelos {}".format(self.en_sefer),  # u"אונקלוס",
            'undefined': None,
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
        if isinstance(ref.text('he').text, list) and all(filter(lambda x: isinstance(x, list), ref.text('he').text)) and any([isinstance(x, int) for deep1 in ref.text('he').text for x in deep1]):
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
            try:
                new_ref = pm.match(tc_list=[ref.text('he'), (comment, 1)], return_obj=True)
                new_ref = filter(lambda x: x.score > 80,  new_ref)
            except ValueError:
                print u"something wrong with hebrew text of ref: {}".format(ref)
                new_ref = []
        return new_ref

    def change_ref_to_commentary(self, ref, comment_ind):
        ls = LinkSet(ref)
        commentators_on_ref = [x.refs[0] if x.refs[0] != ref.normal() else x.refs[1] for x in ls if Ref(x.refs[0]).is_commentary() or Ref(x.refs[1]).is_commentary()]
        comment_ind = Ref(comment_ind).index.collective_title
        options = []
        interLenR = []
        for comm in commentators_on_ref:
            if comment_ind in Ref(comm).index.title:
                if ref.index.title in Ref(
                        comm).index.title:  # for places that we are looking for Rashi on a diffrent book 125.4
                    options.append(Ref(comm).section_ref())
        if options:
            for r in options:
                interLenR.append((r, len(filter(lambda x: x in ref.normal(), re_split_line(r.normal(), '(\s+|:)')))))
            foundr = max(interLenR)[0]
            return foundr.section_ref()
        if self.en_sefer in comment_ind:
            comment_ind = re.search(u'(.*?) on (?:.*?){}'.format(self.en_sefer), comment_ind).group(1)
            for comm in commentators_on_ref:
                if comment_ind in Ref(comm).index.title:
                    return Ref(comm).section_ref()
        return ref

    def try_parallel_matcher(self, current_source, guess_ref = None, guess_parshan = None):
        if not self.looking_for_matches:
            return False
        # if isinstance(current_source.ref, Ref):
        #     current_source.ref = current_source.ref.normal()
        try:
            try:
                if not current_source.get_sefaria_ref(current_source.ref, parsha):
                    if guess_ref:
                        if re.search(u" on ", current_source.ref):
                            commentator = re.split(u" on ", current_source.ref)[0]
                            ref2check = current_source.get_sefaria_ref(u"{} on {}".format(commentator, re.split(u" on ", current_source.ref)[1] if re.search(u" on ", guess_ref) else guess_ref), parsha)
                        else:
                            ref2check = current_source.get_sefaria_ref(guess_ref, parsha)
                    else:
                        ref2check = None
                else:
                    ref2check = current_source.get_sefaria_ref(current_source.ref, parsha)
            except InputError:
                if u"Meshech Hochma" in current_source.ref:
                    ref2check = Ref(u"Meshech Hochma, {}".format(self.en_parasha))
            text_to_use = u""
            if isinstance(current_source.text, list):
                current_source.text = current_source.text[-1]
            if self.mode == "fast":
                text_to_use = u" ".join(current_source.text.split()[0:15])
            elif self.mode == "accurate":
                if current_source.text.split() < 75:
                    text_to_use =u" ".join(current_source.text) if isinstance(current_source.text, list) else current_source.text
                else:
                    text_to_use = u" ".join(current_source.text.split()[0:74])
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
                            if current_source.parshan_id == 'undefined':
                                parshan = ref2check.index.title
                            # chenged_ref = Ref(u'{} {}'.format(parshan, u'{}:{}'.format(ref2check.sections[0], ref2check.sections[1]) if len(ref2check.sections)>1 else u'{}'.format(ref2check[0])))
                            assert parshan
                            changed_ref = self.change_ref_to_commentary(ref2check, parshan)
                            if changed_ref !=ref2check:
                                matched1 = self.check_reduce_sources(text_to_use, changed_ref)
                                matched = matched if len(matched)>=len(matched1) else matched1
                        except KeyError:
                            print u"parshan_id_table is missing a key and value for {}, in {}, \n text {}".format(current_source.parshan_id, self.current_file_path, current_source.text)
                            pass
                        except AssertionError as e:
                            print e
                            pass
                        except: # this is here because this small try shouldn't fly all the way to the try of all the PM and not use what it might have found. i know it is not good practice
                            pass
                    # look one level up - todo: is checking level up duplicated?
                    if not matched:  # and parshan is a running parshan, still not matched! מלבים. אברבנל.העמק דבר רלבג
                        if current_source.text.split() < 75:
                            text_to_use = u" ".join(current_source.text) if isinstance(current_source.text,
                                                                                       list) else current_source.text
                        else:
                            text_to_use = u" ".join(current_source.text.split()[0:74])
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

    def run_words_test(self, content, sources, html_sheet):
        remove_html = lambda x: bleach.clean(x, strip=True).replace("<b>", "").replace("</b>", "")
        orig_sources = list(sources)
        content = content.find('div', {"id": 'contentBody'}).get_text().splitlines()
        if parser.english_sheet:
            sources = [source["outsideBiText"] if "outsideBiText" in source.keys() else source["text"]["he"] for source
                       in sources]
        else:
            sources = [source["outsideText"] if "outsideText" in source.keys() else source["text"]["he"] for source
                       in sources]
        sources = [remove_html(source['he']) if type(source) is dict else remove_html(source) for source in sources] #[remove_html(source.decode('utf-8')) if type(source) is str else remove_html(source) for source in sources]
        sources = u" ".join(sources)
        found_lines = []
        for line_n, line in enumerate(content):
            if not line or not " " in line:
                continue
            if len(line.split()) == 2 and u"פסוק" in line:
                continue
            line = line.strip()  # account for get_text errors
            if line not in sources:
                words = line.replace(".", ". ").replace("?", "? ").replace("  ", " ").split()
                flag = 0
                for word in words:
                    if word not in sources:
                        flag += 1
                    if flag == 2:
                        found_lines.append(line)
                        break
        with open(u"reports/text_check.csv", 'a') as fcsv:
            writer = csv.DictWriter(fcsv, [u'sheet', u'missing text'])
            # f.write("Checking {}\n".format(html_sheet))
            if found_lines:
                for line in found_lines:
                    writer.writerow({u'sheet': html_sheet, u'missing text':line})

    def bs4_reader(self, file_list_names, post = False, add_to_title = u'', only_sheet_links=False):
        """
        The main BeautifulSoup reader function, that etrates on all sheets and creates the obj, probably should be in it's own file
        :param self:
        :return:
        """
        found_tables = set()
        sheets = OrderedDict()
        for html_sheet in file_list_names:
            try:
                parser.current_file_path = html_sheet
                parser.matches[parser.current_file_path] = []
                parser.non_matches[parser.current_file_path] = []
                parser.index_not_found[parser.current_file_path] = []
                parser.ref_not_found[parser.current_file_path] = []
                with codecs.open(u'reports/parshan_id_table.txt', 'a', encoding='utf-8') as fp:
                    fp.write(u"{} \n".format(html_sheet))
                with codecs.open(u"{}".format(html_sheet), 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    file_content = file_content.replace("<U>", "<B>").replace("</U>", "</B>").replace("<u>","<b>").replace("</u>", "</b>")
                    if re.search(u'</P[^>]*?>(\s*[^<\s]+?[^<]*)<', file_content, flags=re.IGNORECASE):
                        # for missing in re.findall(u'</P[^>]*?>(\s*[^<\s]+?[^<]*)<', file_content):
                        #     print "missing",  missing
                        compiled = re.compile(u'(</P[^>]*?>)(\s*[^<\s]+?[^<]*)(<)', flags=re.IGNORECASE)
                        file_content = re.sub(compiled, ur'''\1<p>\2</p>\3''', file_content)
                    def get_ssn(matchObj):
                        ssn = int(matchObj.group(2))
                        text = matchObj.group(3)
                        texts = [text]
                        if re.search(u'u', text, flags=re.IGNORECASE):
                            texts.append(re.sub(u'u', u'b', text, flags=re.IGNORECASE))
                        for text in texts:
                            try:
                                # id = parser.map_ssn_url[ssn]
                                id=ssn
                                new = u'''<a href="/sheets/{}" target="_blank" class="refLink">{}</a>'''.format(id, text)
                            except KeyError:
                                return matchObj.group(0)  # we don't have the sheet it connects to, so return the original.
                            parser.ssn_dicts.append({u"linked_to_id": id, u"text": text, u"linked_text": new})
                        # return new
                    for matchlink in re.finditer(u'(<a href="http://www\.nechama\.org\.il/pages/(\d+?)\.html.*?">(.*?)</a>)', file_content, flags=re.IGNORECASE):
                        get_ssn(matchlink)

                    for snunitlink in re.finditer(u'(<a href="(?P<a_tag>http://kodesh.snunit.k12.il/.*?)>(?P<words>.*?)</a>)', file_content, flags=re.IGNORECASE):
                        r = Section.exctract_pasuk_from_snunit(snunitlink.group('a_tag'))
                        print u"new snunit ref: {} on word: {}".format(r,snunitlink.group('words'))
                        if r:
                            parser.snunit_outside_texts.append({u"words":snunitlink.group('words'), u"ref":r})
                    # file_content = re.sub(u'(<a href="http://www\.nechama\.org\.il/pages/(\d+?)\.html.*">(.*?)</a>)', get_ssn, file_content, flags=re.IGNORECASE)
                    print html_sheet

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
                sheet.links_to_other_sheets = bool(content.find_all("a", {"href": re.compile("(^http.*?nechama.org.il/pages/)|(/sheets/)")}))

                if only_sheet_links and not sheet.links_to_other_sheets:
                    return
                else:
                    print content.find_all("a", {"href": re.compile("^http.*?nechama.org.il/pages/")})
                sheets[html_sheet] = sheet
                body_dict = dict_from_html_attrs(content.find('div', {'id': "contentBody"}))
                sheet.div_sections.extend([v for k, v in body_dict.items() if re.search(u'ContentSection_\d', k)]) # check that these come in in the right order
                sheet.sheet_remark = body_dict['sheetRemark'].text
                # sheet.sheet_remark = str(body_dict['sheetRemark'])
                # sheet.sheet_remark = bleach.clean(sheet.sheet_remark, tags=["a"], strip=True)
                sheet.parse_as_text()
                sheet.create_sheetsources_from_objsource()
                amt = self.check_tables(sheet.sources, sheet.sections)
                sheet.prepare_sheet(add_to_title, post=post)
                if amt > 0:
                    found_tables.add(html_sheet)
                self.run_words_test(content, sheet.sources, html_sheet)
            except Exception, e:
                if parser.catch_errors:
                    self.error_report.write(html_sheet+": ")
                    self.error_report.write(str(sys.exc_info()[0:2]))
                    self.error_report.write("\n")
                    self.error_report.write(traceback.format_exc())
                    self.error_report.write("\n\n")
                else:
                    raise

        return found_tables, sheets

    def check_tables(self, sources, sections):
        num_sections = len(sections)
        num_tables = 0
        for source in sources:
            text = source["outsideText"] if "outsideText" in source.keys() else source["text"]["he"]
            if "<table" in text:
                num_tables += 1
        assert num_tables >= num_sections, "Not enough header tables."
        return num_tables - num_sections

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

    # def create_map_ssn_url(self):
    #     map_ssn_url = dict()
    #     for ssn in (range(1, 1478)):
    #         sheets = db.sheets.find({"$and": [{"tags": "Bilingual"}, {"tags": "{}".format(ssn)}]})
    #         for s in sheets:
    #             map_ssn_url[ssn]=s['id']
    #             break
    #     return map_ssn_url


def dict_from_html_attrs(contents):
    d = OrderedDict()
    for e in [e for e in contents if isinstance(e, element.Tag)]: #for e in [e for e in contents if isinstance(e, element.Tag)]:
        if "id" in e.attrs.keys():
            d[e.attrs['id']] = e
        else:
            d[e.name] = e
    return d

snunit_links = True

if __name__ == "__main__":
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
    english_sheet = False

    posting = True
    individuals = [352] #[112, 113, 105, 106, 75, 109, 13, 110, 15, 16, 17, 85, 86, 111]
  # [1, 259, 5, 774, 14, 273, 27, 35, 37, 299, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 327, 332, 619, 114, 115, 118, 1402, 1403, 1404, 1405, 1406, 1407, 1409, 142, 147, 661, 1440, 169, 172, 174, 204, 210, 246]
#[35, 246, 169, 45, 142, 48, 115, 51, 52, 174, 118, 27, 53] #[1409, 259, 246, 774, 327, 172, 332, 142, 619, 115, 273, 210, 147, 46, 661, 1405, 204, 27, 118, 1440, 35, 37, 169, 299, 44, 45, 174, 47, 48, 49, 50, 51, 52, 53, 54, 55, 114, 1403, 1404, 1402, 1406, 1407]

    #range(1, 1478) #[2, 14, 20, 22, 23, 32, 33, 34, 37, 39, 42, 44, 46, 47, 49, 50, 56, 57, 65, 72, 75, 78, 80, 82, 83, 86, 102, 109, 110, 111, 114, 116, 117, 126, 135, 144, 145, 151, 152, 161, 165, 171, 178, 180, 196, 199, 200, 207, 209, 216, 226, 229, 234, 235, 236, 237, 238, 239, 240, 242, 247, 248, 249, 252, 262, 266, 270, 274, 275, 277, 279, 287, 294, 295, 297, 303, 306, 307, 308, 315, 316, 322, 325, 326, 329, 332, 336, 339, 341, 345, 348, 349, 354, 358, 359, 366, 367, 374, 375, 377, 378, 381, 385, 388, 391, 395, 396, 402, 404, 406, 407, 416]
  #[1409, 259, 774, 44, 142, 147, 174, 27, 1440, 35, 37, 169, 172, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 246, 327, 332, 204, 1407, 619, 114, 115, 118, 1402, 1403, 1404, 1405, 1406, 661]
#range(1341,1479)
#range(10,1478,10)  # reversed(range(1464, 1479)) # [332] range(110, 1479) #[119, 170, 260, 620, 775, 1403, 1404, 1405, 1406, 1407, 1408, 35, 118, 169, 259, 619, 774, 1402, 1403, 1404, 1405, 1406, 1407]
 #976 #range(485, 1479) # range(1022, 1478, 10) #[1075, 1320, 1163]  # [3, 748,452,1073,829,544,277,899,246,490,986,988,717, 1373,  1393,572,71,46,559,892,427]

    found_tables_num = 0
    found_tables = set()
    with open(u"reports/text_check.csv", 'a') as fcsv:
        writer = csv.DictWriter(fcsv, [u'sheet', u'missing text'])
        writer.writeheader()
    for individual in individuals: #range(1321, 1479): #individuals: #range(212, 1400): #  failed on look_for_missing_next: [57, 62. 85, 163]
        got_sheet = None
        for which_parshiot in [genesis_parshiot, exodus_parshiot, leviticus_parshiot, numbers_parshiot, devarim_parshiot]:
            # print u"NEW BOOK"
            for parsha in which_parshiot[1]:
                book = which_parshiot[0]
                parser = Nechama_Parser(en_sefer=book, en_parasha=parsha, mode="accurate", add_to_title=u"Sheet2Sheet", catch_errors=catch_errors, looking_for_matches=True, english_sheet=english_sheet)
                #parser.prepare_term_mapping()  # must be run once locally and on sandbox
                #parser.bs4_reader(["html_sheets/Bereshit/787.html"], post=False)
                if not individual:
                    sheets = [sheet for sheet in os.listdir("html_sheets/{}".format(parsha)) if sheet.endswith(".html")]
                    # anything_before = "7.html"
                    # pos_anything_before = sheets.index(anything_before)
                    # sheets = sheets[pos_anything_before:]
                    # sheets = sheets[sheets.index("163.html")::]
                # sheets = [u"163.html"]
                if individual:
                    got_sheet = parser.bs4_reader([u"html_all/{}.html".format(individual)] if u"{}.html".format(individual) in os.listdir(u"html_sheets/{}".format(parsha)) else [], post=posting, add_to_title=parser.add_to_title, only_sheet_links=False)
                else:
                    found_tables_in_parsha = parser.bs4_reader([u"html_sheets/{}/{}".format(parsha, sheet) for sheet in sheets])# if sheet in os.listdir("html_sheets/{}".format(parsha)) and sheet != "163.html"], post=posting)
                    found_tables = found_tables.union(found_tables_in_parsha)

                if catch_errors:
                    parser.record_report()
                if individual and got_sheet and got_sheet[1]:
                    break
            if individual and got_sheet and got_sheet[1]:
                break
        # print found_tables
        # print word_count
        # with open("sheets_linked_to_sheets.csv", 'w') as f:
        #     writer = UnicodeWriter(f)
        #     writer.writerows(sheets_linked_to_sheets)


