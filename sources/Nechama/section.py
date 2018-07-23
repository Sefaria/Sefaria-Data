#encoding=utf-8

class Section(object):

    def __init__(self, sheet, number):
        self.number = number # which number section am I
        self.sheet = sheet # which sheet is the section on
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
                orig_text = segment.text.replace("\n", "").replace("\r", "")
                if combined_with_prev_line:  # i.e.: "Pasuk 5" is the previous line which gets combined with the current line that has Pasuk 5's content
                    formatted_text = "<b><small>" + combined_with_prev_line + "</b><br/>" + orig_text + "</small>"
                    combined_with_prev_line = None
                else:
                    formatted_text = "<small>" + orig_text + "</small>"
                segments[i] = Parshan().add_text(orig_text, segment_class, pre_text=combined_with_prev_line)
                continue
            elif Nechama_Comment.is_comment(segments, i, self.sheet.important_classes):  # above criteria not met, just an ordinary comment
                segments[i] = Nechama_Comment(relevant_text)
            else:  # must be a Comment
                next_segment_class = segments[i + 1].attrs["class"][0]  # get the class of this ref and it's comment
                self.parse_ref(segment, relevant_text, next_segment_class)
        return segments

    def parse_ref(self, segment, relevant_text, next_segment_class):
        real_title, found_a_tag, a_tag_is_entire_comment = self.get_a_t
class Sheet(object):

    def __init__(self, html, parasha, title, year, ref=None):
        self.html = html
        self.title = title
        self.parasha = parasha
        self.he_year = re.sub(u"שנת", u"", year).strip()
        self.year = getGematria(self.he_year)+5000  # +1240, jewish year is more accurate
        self.sections = []
        self.pesukim = self.get_ref(ref)  # (re.sub(u"(פרק(ים)?|פסוק(ים)?)", u"", ref).strip())
        self.sheet_remark = u""
        self.header_links = None  # this will link to other  nechama sheets (if referred).
        self.quotations = [] #last one in this list is the current ref
        self.current_parsha_ref = ""
        self._term_cache = {}
        self.current_section = 0
        self.sections = []
        self.important_classes = ["parshan", "midrash", "talmud", "bible", "commentary"]
        self.term_mapping = {
            u"""הנצי"ב מוולוז'ין""": u"Haamek Davar on Genesis",
            u"אונקלוס": u"Onkelos Genesis",
            u"שמואל דוד לוצטו": u"Shadal on Genesis",
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
            u"""הרא"ם""": u"Mizrachi, Genesis",
            u"""ר' יוסף בכור שור""": u"Bekhor Shor, Genesis",
            u"בכור שור": u"Bekhor Shor, Genesis",
            u"אברבנאל": u"Abarbanel on Torah, Genesis",
            u"""המלבי"ם""": u"Malbim on Genesis",
            u"משך חכמה": u"Meshech Hochma, Bereshit",
            u"רבנו בחיי": u"Rabbeinu Bahya, Bereshit",
            u'רב סעדיה גאון': u"Saadia Gaon on Genesis"

        }

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
            if div['id'] == "sheetRemark" and div.text.replace(" ","") != "":  # comment of hers that appears at beginning of section
                # refs_to_other_sheets = self.get_links_to_other_sheets(div)
                intro_segment = div
                intro_tuple = ("nechama", "<b>" + intro_segment.text + "</b>", "")
            elif "ContentSection" in div['id']:  # sections within source sheets
                self.current_section += 1
                new_section = Section(self, self.current_section)
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
                self.quotations = [["bible", self.quotation_stack[0]]]
                self.sections.append(segments)



class Segments(object):

    def __init__(self, type):
        self.type = type


class Parshan(object):

    def __init__(self, section, segment_class, ref):
        self.parshan_name = u""
        self.about_parshan_ref = u"" #words of nechama in regards to the parshan or this specific book, that we will lose since it is not part of our "ref" system see 8.html sec 1. "shadal"
        self.perek = u""
        self.pasuk = u""
        self.ref = ref  #this can be blank indicating our parser couldn't figure out what the ref is
        self.nechama_comments = u""
        self.nechama_q = [] #list of Qustion objs about this Parshan seg
        self.section = section #which section I belong to
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
            self.section.sheet.index_not_found[self.last_comm_index_not_found].append((self.section.current_parsha_ref, orig))
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
        return isinstance(segment, element.Tag) and segment.name == "table" and\
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

    def __init__(self, section, text):
        self.section = section
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
        return not next_comment_parshan_or_bible or not this_comment_could_be_refag_from_ref(segment, relevant_text)
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
            self.last_comm_index_not_found = found_a_tag.text
        else:
            self.last_comm_index_not_found_bool = True



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
            poss_ref = self.pasuk_in_parsha_pasukim(new_pasuk)
            if poss_ref:
                self.current_perek = poss_ref.sections[0]
                self.current_pasuk = poss_ref.sections[1]
            else:
                print
                self.current_parsha_ref = ["bible", u"{} {}".format(self.current_sefer, self.current_perek)]
        return True, self.current_perek, new_pasuk

    def set_current_perek_pasuk(self, text, next_segment_class, is_tanakh=True):
        text = text.replace(u"פרקים", u"Perek").replace(u"פרק ", u"Perek ").replace(u"פסוקים", u"Pasuk").replace(
            u"פסוק ", u"Pasuk ").strip()
        digit = re.compile(u"^.{1,2}[\)|\.]").match(text)
        # if next_segment_class == "parshan":
        #     sefer = u"Parshan on {}".format(self.current_sefer)
        # elif next_segment_class == "bible":
        sefer = self.sheet.current_sefer

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
            new_parshan = Parshan(self, "bible", u"{} {}:{}".format(self.current_sefer, new_perek, new_pasuk))
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