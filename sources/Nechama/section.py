from sheets_steve import *

class Section(object):

    def __init__(self):
        self.letter = ""
        self.name = ""
        self.segments = []  # list of Segment objs
        self.first_bible_ref = "" # used to link everything below it
        self.sheet = None # which sheet do I belong to?
        self.last_comm_index_not_found_bool = False # if previous segment was supposed to be a commentator but couldn't find it in library
        self.last_comm_index_not_found = "" # name of commentator that couldnt be found in library


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
            # when she is quoting a reference to a text, this function sets segments[i]
            if (is_perek_pasuk_ref or real_title or found_ref_in_string):
                if not a_tag_is_entire_comment and found_ref_in_string == "" and len(relevant_text.split()) >= 6:
                    # edge case where you found the ref but Nechama said something else in addition to the ref
                    # so we want to keep the text
                    combined_with_prev_line = relevant_text
                    # could be Comment.about = relevant_text; Comment.ref = ref; Comment.ref_in_library = True;
                segments[i] = "reference"
            elif found_a_tag:
                # found no reference but did find an a_tag so this is a ref so keep the text
                combined_with_prev_line = relevant_text
                # could be Comment.ref = relevant_text; Comment.about = ""; Comment.ref_in_library = False;
                segments[i] = "combined but not reference"
                self.last_comm_index_not_found = found_a_tag.text
            else:
                self.last_comm_index_not_found_bool = True
                segments[i] = ("nechama", relevant_text, "")
            return combined_with_prev_line
        combined_with_prev_line = None
        prev_was_quote = None
        for i, segment in enumerate(segments):
            relevant_text = self.format(self.relevant_text(segment))  # if it's Tag, tag.text; if it's NavigableString, just the string
            if Question.is_question(segment):
                segments[i] = Question(segment)
            elif Header.is_header(segment)
                segments[i] = Header(segment)
            elif segment.attrs["class"] in [["RT"],["RTBorder"]]:  # these tables we want as they are so just str(segment)
                    segments[i] = ("nechama", str(segment), "")
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
            elif Nechama_Comment.is_comment(segments, i, self.sheet):  # above criteria not met, just an ordinary comment
                segments[i] = Nechama_Comment(relevant_text)
            else:  # must be a Comment
                next_segment_class = segments[i + 1].attrs["class"][0]  # get the class of this ref and it's comment
                real_title, found_a_tag, a_tag_is_entire_comment, a_tag_in_long_comment \
                    = self.get_a_tag_from_ref(segment, relevant_text)

                is_perek_pasuk_ref, real_title, found_ref_in_string \
                    = self.check_ref_and_add_to_quotation_stack(next_segment_class, relevant_text, real_title)

                combined_with_prev_line = set_ref_segment(combined_with_prev_line)
                prev_was_quote = ""
        return segments


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
            elif len(p.text.split()) == 1 and re.compile(u"^.{1,2}[\)|\.]").match(p.text):  # make sure it's in form 1. or ש.
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
        children_w_contents = [el for el in segment.contents if self.relevant_text(el).replace("\n", "").replace("\r", "").replace(": ", "").replace(":", "") != "" and len(self.relevant_text(el)) > 2]
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