#encoding=utf-8

import django
django.setup()

import requests
import re
import os
from sources.functions import getGematria
from sefaria.model import *
from sefaria.system.exceptions import InputError
from collections import OrderedDict
from bs4 import BeautifulSoup, element
from segments import *

class Sheet(object):

    def __init__(self, html, parasha, title, year, ref, sefer, perek_info):
        self.html = html
        self.title = title
        self.parasha = parasha
        self.en_parasha = Term().load({"titles.text": parasha}).name
        self.sefer, self.perakim, self.pasukim = self.extract_perek_info(perek_info)
        self.en_sefer = library.get_index(sefer).title
        self.he_year = re.sub(u"שנת", u"", year).strip()
        self.year = getGematria(self.he_year) + 5000  # +1240, jewish year is more accurate
        self.sections = []
        self.pesukim = self.get_ref(ref)  # (re.sub(u"(פרק(ים)?|פסוק(ים)?)", u"", ref).strip())
        self.sheet_remark = u""
        self.header_links = None  # this will link to other  nechama sheets (if referred).
        self.quotations = []  # last one in this list is the current ref
        self.current_parsha_ref = ""
        self._term_cache = {}
        self.current_section = 0
        self.sections = []
        self.important_classes = ["parshan", "midrash", "talmud", "bible", "commentary"]
        self.term_mapping = {
            u"""הנצי"ב מוולוז'ין""": u"Haamek Davar on {}".format(self.en_sefer),
            u"אונקלוס": u"Onkelos {}".format(self.en_sefer),
            u"שמואל דוד לוצטו": u"Shadal on {}".format(self.en_sefer),
            u"מורה נבוכים א'": u"Guide for the Perplexed, Part 1",
            u"מורה נבוכים ב'": u"Guide for the Perplexed, Part 2",
            u"מורה נבוכים ג'": u"Guide for the Perplexed, Part 3",
            u"תנחומא": u"Midrash Tanchuma, Bereshit",
            u"בעל גור אריה": u"Gur Aryeh on Bereishit",
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
            u'רב סעדיה גאון': u"Saadia Gaon on {}".format(self.en_sefer)

        }

    def extract_perek_info(self, perek_info):
        def get_pasukim_for_perek(sefer, perek):
            en_sefer = library.get_index(sefer).title
            return str(len(Ref(u"{} {}".format(en_sefer, perek)).all_segment_refs()))

        #three formats: Perek 2; Perek 2, Pasuk 3-9; Perek 2, 4 - Perek 3, 2 (last one may lose pasuk info as well
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

        return (sefer, pereks, pasuks)

    def pasuk_in_parsha_pasukim(self, new_pasuk, perakim=None):
        if perakim is None:
            perakim = self.perakim
        for perek in perakim:
            possible_ref = Ref("Genesis " + perek + ":" + new_pasuk)
            if self.pasukim.contains(possible_ref):
                return possible_ref
        return None

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

    def get_a_tag_from_ref(self, segment, relevant_text):
        if segment.name == "a":
            a_tag = segment
        else:
            a_tag = segment.find('a')

        real_title = ""

        # if a_tag and segment.find("u") and a_tag.text != segment.find("u").text: #case where
        a_tag_is_entire_comment = a_tag_occurs_in_long_comment = False
        if a_tag:
            a_tag_is_entire_comment = len(a_tag.text.split()) == len(segment.text.split())
            real_title = self.sheet.get_term(a_tag.text)
        elif relevant_text in self.sheet.term_mapping:
            real_title = self.sheet.term_mapping[relevant_text]
        if not real_title and self.RT_Rashi:  # every ref in RT_Rashi is really to Rashi
            real_title = "Rashi on {}".format(self.sheet.current_sefer)
        return (real_title, a_tag, a_tag_is_entire_comment)

    def parse_as_text(self):
        intro_segment = intro_tuple = None
        for div in self.sections:
            if div['id'] == "sheetRemark" and div.text.replace(" ",
                                                               "") != "":  # comment of hers that appears at beginning of section
                # refs_to_other_sheets = self.get_links_to_other_sheets(div)
                intro_segment = div
                intro_tuple = ("nechama", "<b>" + intro_segment.text + "</b>", "")
            elif "ContentSection" in div['id']:  # sections within source sheets
                self.current_section += 1
                new_section = SectionParser(self, self.current_section)
                self.sections.append(new_section)
                assert str(self.current_section) in div['id']

                if div.text.replace(" ", "") == "":
                    continue

                # removes nodes with no content
                segments = new_section.get_children_with_content(div)

                # blockquote is really just its children so get replace it with them
                # and tables  need to be handled recursively
                segments = new_section.check_for_blockquote_and_table(segments, level=2)

                # here is the main logic of parsing

                segments = new_section.classify_segments(segments)
                self.RT_Rashi = False
                if intro_segment:
                    segments.insert(0, intro_tuple)
                    intro_segment = None

                # assert len(self.quotations) == self.current_pos_in_quotation_stack+1
                # assert 3 > len(self.quotation_stack) > 0
                # if len(self.quotation_stack) >= 2:
                #    segments = self.add_links_from_intro_to_many_comments(segments)
                self.sections.append(segments)






class SectionParser(object):

    def __init__(self, sheet, number):
        self.number = number  # which number section am I
        self.sheet = sheet  # which sheet is the section on
        self.letter = ""
        self.name = ""
        self.segments = []  # list of Segment objs
        self.first_bible_ref = ""  # used to link everything below it
        self.last_comm_index_not_found_bool = False  # if previous segment was supposed to be a commentator but couldn't find it in library
        self.last_comm_index_not_found = ""  # name of commentator that couldnt be found in library
        self.ref_not_found = {}
        self.RT_Rashi = False

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
        combined_with_prev_line = None
        prev_was_quote = None
        new_parshan = None
        for i, segment in enumerate(segments):
            relevant_text = self.format(
                self.relevant_text(segment))  # if it's Tag, tag.text; if it's NavigableString, just the string
            if Question.is_question(segment):
                segments[i] = Question(self, segment)
            elif Header.is_header(segment):
                segments[i] = Header(self, segment)
            elif Table.is_table(segment):  # these tables we want as they are so just str(segment)
                segments[i] = Table(self, segment)
            elif isinstance(segment, element.Tag) and segment.has_attr("class"):
                # this is a comment by a commentary, bible, or midrash
                segment_class = segment.attrs["class"][0]  # is it parshan, bible, or midrash?
                assert len(segment.attrs["class"]) == 1, "More than one class"
                segments[i] = new_parshan.add_text(segment, segment_class)
                continue
            elif Nechama_Comment.is_comment(segments, i,
                                            self.sheet.important_classes):  # above criteria not met, just an ordinary comment
                segments[i] = Nechama_Comment(relevant_text)
            else:  # must be a Comment
                next_segment_class = segments[i + 1].attrs["class"][0]  # get the class of this ref and it's comment
                new_parshan = self.parse_ref(segment, relevant_text, next_segment_class)
        return segments

    def get_a_tag_from_ref(self, segment, relevant_text):
        if segment.name == "a":
            a_tag = segment
        else:
            a_tag = segment.find('a')

        real_title = ""

        # if a_tag and segment.find("u") and a_tag.text != segment.find("u").text: #case where
        a_tag_is_entire_comment = a_tag_occurs_in_long_comment = False
        if a_tag:
            a_tag_is_entire_comment = len(a_tag.text.split()) == len(segment.text.split())
            real_title = self.sheet.get_term(a_tag.text)
        elif relevant_text in self.sheet.term_mapping:
            real_title = self.sheet.term_mapping[relevant_text]
        if not real_title and self.RT_Rashi:  # every ref in RT_Rashi is really to Rashi
            real_title = "Rashi on {}".format(self.sheet.current_sefer)
        return (real_title, a_tag, a_tag_is_entire_comment)

    def parse_ref(self, segment, relevant_text, next_segment_class):
        real_title, found_a_tag, a_tag_is_entire_comment = self.get_a_tag_from_ref(segment, relevant_text)
        new_parshan, found_ref_in_string = self.check_ref_and_create_new_parshan(next_segment_class, relevant_text,
                                                                                 real_title)
        if new_parshan.get_ref():
            if not a_tag_is_entire_comment and found_ref_in_string == "" and len(relevant_text.split()) >= 6:
                # edge case where you found the ref but Nechama said something else in addition to the ref
                # so we want to keep the text
                new_parshan.about_parshan_ref = relevant_text
        elif found_a_tag:
            # found no reference but did find an a_tag so this is a ref so keep the text
            new_parshan.about_parshan_ref = relevant_text
        else:
            new_parshan.ref = ""

        return new_parshan

    def _get_refs_in_string(self, strings, next_segment_class, add_if_not_found=True):
        not_found = []
        for string in strings:
            orig = string
            string = "(" + string.replace(u"(", u"").replace(u")", u"") + ")"
            words_to_replace = [u"פרשה", u"*", chr(39), u"פרק", u"פסוק", u"השווה"]
            for word in words_to_replace:
                string = string.replace(u"ל" + word, u"")
                string = string.replace(word, u"")
            string = string.replace(u"  ", u" ")
            string = string.strip()
            refs = library.get_refs_in_string(string)
            if refs:
                new_parshan = Parshan(self, next_segment_class, refs[0].normal())
                assert len(refs) <= 1 or u"השווה" in orig
                return string[1:-1]  # remove ( )
            else:
                not_found.append(orig)
        if len(not_found) == len(strings):
            self.ref_not_found[strings[-1]] += 1
        return ""

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
            poss_ref = self.sheet.pasuk_in_parsha_pasukim(new_pasuk)
            if poss_ref:
                self.current_perek = poss_ref.sections[0]
                self.current_pasuk = poss_ref.sections[1]
            else:
                print
                self.current_parsha_ref = ["bible", u"{} {}".format(self.sheet.sefer, self.current_perek)]
        return True, self.current_perek, new_pasuk

    def set_current_perek_pasuk(self, text, next_segment_class, is_tanakh=True):
        text = text.replace(u"פרקים", u"Perek").replace(u"פרק ", u"Perek ").replace(u"פסוקים", u"Pasuk").replace(
            u"פסוק ", u"Pasuk ").strip()
        digit = re.compile(u"^.{1,2}[\)|\.]").match(text)
        sefer = self.sheet.sefer

        if digit:
            text = text.replace(digit.group(0), "").strip()
        text += " "  # this is hack so that reg ex works

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
                poss_ref = self.sheet.pasuk_in_parsha_pasukim(new_pasuk, perakim=[new_perek])
                if poss_ref:
                    self.current_perek = poss_ref.sections[0]
                    self.current_pasuk = poss_ref.sections[1]
                    assert str(poss_ref.sections[0]) == new_perek
                    assert str(poss_ref.sections[1]) == new_pasuk
                    self.current_parsha_ref = ["bible", u"{} {}".format(self.sefer, self.current_perek)]
                else:
                    print
            return True, new_perek, new_pasuk
        return False, self.current_perek, self.current_pasuk

    def check_ref_and_create_new_parshan(self, next_segment_class, relevant_text, real_title):
        found_ref_in_string = ""

        # check if it's in Perek X, Pasuk Y format and set perek and pasuk accordingly
        is_tanakh = (relevant_text.startswith(u"פרק ") or relevant_text.startswith(u"פסוק ") or
                     relevant_text.startswith(u"פרקים ") or relevant_text.startswith(u"פסוקים "))
        is_perek_pasuk_ref, new_perek, new_pasuk = self.set_current_perek_pasuk(relevant_text, next_segment_class,
                                                                                is_tanakh)

        # now add to quotation stack either based on real_title or based on self.current_parsha_ref
        if real_title:  # a ref to a commentator that we have in our system
            if new_pasuk:
                new_parshan = Parshan(self, next_segment_class,
                                      u"{} {}:{}".format(real_title, new_perek, new_pasuk))
            else:
                new_parshan = Parshan(self, next_segment_class, u"{} {}".format(real_title, new_perek))
        elif not real_title and is_tanakh:  # not a commentator, but instead a ref to the parsha
            new_parshan = Parshan(self, "bible", u"{} {}:{}".format(self.sheet.sefer, new_perek, new_pasuk))
        elif len(relevant_text.split()) < 8:  # not found yet, look it up in library.get_refs_in_string
            found_ref_in_string = self._get_refs_in_string([relevant_text], next_segment_class,
                                                           add_if_not_found=False)
            new_parshan = Parshan(self, next_segment_class, found_ref_in_string)
        else:
            new_parshan = Parshan(self, next_segment_class, "")
        return new_parshan, found_ref_in_string

    def relevant_text(self, segment):
        if isinstance(segment, element.Tag):
            return segment.text
        return segment

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

    def get_children_with_content(self, segment):
        # determine if the text of segment is blank or practically blank (i.e. just a \n or :\n\r) or is just empty space less than 3 chars
        children_w_contents = [el for el in segment.contents if
                               self.relevant_text(el).replace("\n", "").replace("\r", "").replace(": ", "").replace(
                                   ":", "") != "" and len(self.relevant_text(el)) > 2]
        return children_w_contents

    def check_for_blockquote_and_table(self, segments, level=2):
        new_segments = []
        tables = ["table", "tr"]
        for i, segment in enumerate(segments):
            if isinstance(segment, element.Tag):
                class_ = segment.attrs.get("class", [""])[0]
            else:
                new_segments.append(segment)
                continue
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

    def remove_hyper_links(self, html):
        all_a_links = re.findall("(<a href.*?>(.*?)</a>)", html)
        for a_link_and_text in all_a_links:
            a_link, text = a_link_and_text
            html = html.replace(a_link, text)
        return html

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
        perek_info = content.find("p", {"id": "pasuk"}).text
        top_dict = dict_from_html_attrs(content.find('div', {'id': "contentTop"}).contents)
        # print 'len_content type ', len(top_dict.keys())
        sheet = Sheet(html_sheet, top_dict["paging"].text, top_dict["h1"].text, top_dict["year"].text, top_dict["pasuk"].text, u"Genesis", perek_info)
        sheets[html_sheet] = sheet
        body_dict = dict_from_html_attrs(content.find('div', {'id': "contentBody"}))
        sheet.sections.extend([v for k, v in body_dict.items() if re.search(u'ContentSection_\d', k)]) # check that these come in in the right order
        sheet.sheet_remark = body_dict['sheetRemark'].text
        sheet.parse_as_text()

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
    #     self.sefer, self.current_perakim, self.current_pasukim = self.extract_perek_info(content)
    #     self.sefer = library.get_index(self.sefer)
    #     self.current_alt_titles = self.sefer.nodes.get_titles('en')
    #     self.sefer = self.sefer.title
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
    #     self.current_parsha_ref = ["bible", u"{} {}".format(self.sefer, self.current_perek)]
    #     self.add_to_quotation_stack(self.current_parsha_ref)
    #     self.sheets[parsha][self.current_en_year] = (
    #     self.current_url, hebrew_year, self.sefer, self.current_perakim, self.parse_as_text(text))
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
