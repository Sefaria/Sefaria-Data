#encoding=utf-8
from sources.functions import *
from collections import Counter

class Metsudah_Parser:
    def __init__(self, en_title, he_title, cats, vtitle="", vsource="", input_text="", depth=2, node_separator=","):
        self.en_title = en_title
        self.he_title = he_title
        self.categories = cats
        self.input_text = input_text
        self.current_he_ja_node = ""
        self.current_en_ja_node = ""
        self.ja_nodes = []
        self.root_node = SchemaNode()
        self.vtitle = vtitle
        self.vsource = vsource
        self.prev_line_instruction = False
        self.text = {"en": {}, "he": {}} #"en" -> english nodes -> list of english comments; "he" -> english_nodes -> list of hebrew comments
        self.en_to_he = {} #which english corresponds to which hebrew node
        self.en_ja_times = 0
        self.prev_line_en_title = None #previous line having an English title means next line must be Hebrew title
        self.schema = self.curr_schema = SchemaNode()
        self.lengths_off = {} #keep track of which sections have problematic length diff between english and hebrew
        self.index = None
        self.depth = depth #how many levels of nodes until the text; NOT depth that is found on JaggedArrayNodes
        self.headers = ["<@0{}>".format(i+1) for i in range(self.depth)] #headers derived from depth of text
        self.next_line = ""
        self.node_separator = node_separator #character that separates nodes in ref: "Sefer HaYashar, Introduction"
        self.notes = []
        self.chapters_with_ftnotes = []
        self.instruction_tags = ["<M in>", "<M ex>", "@ex", "@in"]#, "<M t2>", "<M t1>"]
        self.lines_starting_sections = []



    def pre_parse(self):
        orig_text = list(open(self.input_text))
        bad_chars = Counter()
        replacements = [("׀", "—"), ("_", "-"), ("±", "-"), ("<TIE>", " "), ("<IT>", "<i>"),
                        ("<ITC>", "</i>")]
        he_replacements = [("r", "ע"), ("H", "לֹּ"), ("G", "לֹ"), ("x", "רֹּ"), ("§", "ךָ")]
        it_only = []
        itc_only = []
        for line_n, line in enumerate(orig_text):
            #first remove non-html and non-ftnote related tags
            orig_text[line_n] = self.replace_tags(line, skip_html=True, skip_ftnotes=True, skip_header=True, skip_language=True)

            #now remove extra <i>s and replace replacements
            for replacement in replacements:
                orig_text[line_n] = orig_text[line_n].replace(replacement[0], replacement[1])
            if "<i>" in orig_text[line_n] and not "</i>" in orig_text[line_n]:
                orig_text[line_n] = orig_text[line_n].replace("<i>", "")
            elif "</i>" in orig_text[line_n] and not "<i>" in orig_text[line_n]:
                orig_text[line_n] = orig_text[line_n].replace("</i>", "")

            #for hebrew text, do he_replacements only in hebrew lines and in hebrew lines, only in hebrew words
            if not any_hebrew_in_str(orig_text[line_n]):
                continue
            words = orig_text[line_n].split(" ")
            new_words = []
            for word_n, word in enumerate(words):
                if not any_hebrew_in_str(word):
                    new_words.append(word)
                    continue
                for replacement in he_replacements:
                    word = word.replace(replacement[0], replacement[1])
                new_words.append(word)
            orig_text[line_n] = " ".join(new_words)
                

        self.input_text = orig_text


    def combine_titles(self):
        # If two headers come one after the other, assume it's really one title and combine them
        # such as: "Maariv Service", "for Shabbos and Yom Tov" should be combined
        running_header_count = 0
        prev_depth = -1
        new_text = []
        for line_n, line in enumerate(self.input_text):
            curr_depth = self.is_header(line)
            if running_header_count == 0 and curr_depth > 0:
                running_header_count = 1
            elif prev_depth == curr_depth and curr_depth > 0:
                running_header_count += 1
            else:
                running_header_count = 0

            assert 0 <= running_header_count < 8, "Titles are assumed to only be split between 2-6 lines not {}".format(
                running_header_count)
            if running_header_count in range(3, 7): #lines 3-7 are headers that need to be combined
                if running_header_count % 2 == 0: #Even is Hebrew
                    new_text[-1] += " "+line
                else:                           #Odd is English
                    new_text[-2] += " "+line
            elif running_header_count < 3:
                new_text.append(line)
            prev_depth = curr_depth

        self.input_text = new_text


    def parse_into_en_and_he_lists(self):
        curr_depth = 0
        curr_ref = self.en_title
        curr_ftnote = prev_ftnote = 0
        self.schema = self.curr_schema = self.create_new_node(self.en_title, self.en_title, self.he_title)
        self.prev_line_instruction = False
        for line_n, line in enumerate(self.input_text):
            line = line.replace("\r\n", "")
            if line_n+1 < len(self.input_text):
                self.next_line = self.input_text[line_n+1]
            line = line.replace("’", "'").replace('﻿', "")
            new_depth = self.is_header(line)
            if new_depth:
                # if new_depth: this is really checking if we have a header;
                # set up the section of text under this header of a particular depth and then continue
                curr_ref, curr_depth = self.set_current_ja(line, curr_ref, new_depth, curr_depth)
                continue
            if not self.current_en_ja_node:
                # haven't gotten to the first header, so nothing to parse
                continue
            ftnote_match = re.findall("@n1.*?(\d+)@n2", line)
            if ftnote_match:
                curr_ftnote = int(ftnote_match[0])
                if curr_ftnote < prev_ftnote or prev_ftnote == 0:
                    #starting over a new section...
                    self.lines_starting_sections.append(line)
                prev_ftnote = curr_ftnote
                if self.current_en_ja_node not in self.chapters_with_ftnotes:
                    #store order of chapters that have footnotes
                    self.chapters_with_ftnotes.append(self.current_en_ja_node)
            instruction, line = self.is_instruction(line)
            temp_line = self.replace_tags(line)  # temp_line needs to be tagless
            has_english = any_english_in_str(temp_line)
            has_hebrew = any_hebrew_in_str(temp_line)
            if instruction or (has_hebrew and has_english):
                self.add_line(line, 'en')
                self.add_line("", 'he')
            elif has_english:
                self.add_line(line, 'en')
                assert instruction is False
            elif any_hebrew_in_str(line):
                self.add_line(line, 'he')
                assert instruction is False
            self.prev_line_instruction = instruction
            if abs(len(self.text['en'][self.current_en_ja_node]) - len(self.text['he'][self.current_en_ja_node])) >= 2:
                if self.current_en_ja_node not in self.lengths_off.keys():
                    self.lengths_off[self.current_en_ja_node] = line


    def is_instruction(self, line):
        instruction = any([tag in line for tag in self.instruction_tags])
        if instruction:
            return True, "<small>{}</small>".format(line)
        elif self.prev_line_instruction and "<EM>" in line:
            if len(self.text['en'][self.current_en_ja_node]) > 0 and "<small>" in self.text['en'][self.current_en_ja_node][-1]:
                self.text['en'][self.current_en_ja_node][-1] = self.text['en'][self.current_en_ja_node][-1].replace("<small>", "").replace("</small>", "")
            return True, line
        return False, line

    def replace_tags(self, line, skip_html=False, skip_ftnotes=False, skip_header=False, skip_language=False):
        html = ["<i>", "<b>", "</i>", "</b>", "<br>", "<small>"]
        language = ["<ENG>", "<EN>", "<HE>", "<HEB>"]
        ftnotes = ["@n1", "@n2"]
        ftnote_pattern = "<\*\d+>"
        headers = self.instruction_tags + self.headers

        tags_in_line = re.findall("<.*?>|@[a-zA-Z0-9]{1,2}", line)
        for tag in tags_in_line:
            remove = True
            if skip_ftnotes and (tag in ftnotes or re.findall(ftnote_pattern, tag)):
                remove = False
            if skip_html and tag in html:
                remove = False
            if skip_header and tag in headers:
                remove = False
            if skip_language and tag in language:
                remove = False
            if remove:
                line = line.replace(tag, "")

        forbidden_in_node_titles = ["."]
        for char in forbidden_in_node_titles:
            line = line.replace(char, "")
        return line

    def is_header(self, line):
        # if header, return depth; otherwise 0
        for h in self.headers:
            if h in line:
                return int(h.replace("<@0", "").replace(">", ""))
        return 0

    def set_current_ja(self, line, curr_ref, new_depth, curr_depth):
        if not self.prev_line_en_title:
            line = self.replace_tags(line).strip()
            if any_hebrew_in_str(line):
                print line
                return curr_ref, curr_depth
            curr_ref, curr_depth = self.set_curr_ref(curr_ref, line, new_depth, curr_depth)
            self.current_en_ja_node = curr_ref
            self.text["en"][self.current_en_ja_node] = []
            self.text["he"][self.current_en_ja_node] = []
            self.prev_line_en_title = self.current_en_ja_node
        elif any_hebrew_in_str(line) and self.prev_line_en_title:
            self.current_he_ja_node = self.replace_tags(line.decode('utf-8')).strip()
            assert self.prev_line_en_title
            self.en_to_he[self.prev_line_en_title] = self.current_he_ja_node
            self.prev_line_en_title = None
        return curr_ref, curr_depth


    def set_curr_ref(self, curr_ref, curr_line, new_depth, curr_depth):
        # 3 cases: new_depth is higher, equal, or lower than curr_depth
        assert new_depth in [i+1 for i in range(self.depth)]
        assert curr_depth in [i+1 for i in range(self.depth)] or curr_depth is 0 # it is 0 at the start
        assert new_depth - curr_depth < 2
        diff = 0
        if new_depth - curr_depth == 1:
            diff = 0
        if new_depth == curr_depth:
            diff = 1
        elif new_depth < curr_depth:
            diff = 1 + curr_depth - new_depth

        #remove as many sections from curr_ref as diff
        while diff > 0:
            diff -= 1
            last_comma = curr_ref.rfind(self.node_separator)
            curr_ref = curr_ref[0:last_comma]
            self.curr_schema = self.curr_schema.parent

        curr_ref += "{} {}".format(self.node_separator, curr_line)
        new_node = self.create_new_node(curr_ref, curr_line, self.next_line)
        self.curr_schema.append(new_node)
        self.curr_schema = new_node
        return curr_ref, new_depth


    def create_new_node(self, curr_ref, en_title, he_title):
        he_title = self.replace_tags(he_title).strip()
        this_depth = len(curr_ref.split(self.node_separator)) - 1
        assert this_depth in range(self.depth+1)
        new_node = None
        if self.depth == this_depth:
            new_node = JaggedArrayNode()
            new_node.add_structure(["Paragraph"])
        elif self.depth > this_depth:
            new_node = SchemaNode()
        new_node.add_primary_titles(en_title, he_title)
        return new_node


    def add_line(self, line, lang):
        #first just add line to he and en dictionaries
        self.text[lang][self.current_en_ja_node].append(line)

        #determine if one language has at least 2 more comments than the other and then attempt to correct it
        other = "en" if lang == "he" else "he"
        diff = len(self.text[lang][self.current_en_ja_node]) - len(self.text[other][self.current_en_ja_node])
        if diff >= 2:
            self.add_line("", other)


    def post_text(self, server):
        for lang in ["en", "he"]:
            for ref, text in self.text[lang].items():
                ref = ref.replace(self.node_separator, ",")
                send_text = {"text": text, "versionTitle": self.vtitle, "versionSource": self.vsource, "language": lang}
                post_text(ref, send_text, server=server)


    def create_schema(self):
        def make_leaf_nodes_jagged_array(node):
            #makes sure that leaf nodes are JA nodes
            if node.children:
                for i, child in enumerate(node.children):
                    node.children[i] = make_leaf_nodes_jagged_array(child)
                return node
            else:
                if not isinstance(node, JaggedArrayNode):
                    new_node = JaggedArrayNode()
                    en, he = node.primary_title("en"), node.primary_title("he")
                    new_node.add_primary_titles(en, he)
                    new_node.add_structure(["Paragraph"])
                    return new_node
                else:
                    return node

        make_leaf_nodes_jagged_array(self.schema)
        self.schema.validate()
        self.index = {
            "title": self.en_title,
            "schema": self.schema.serialize(),
            "categories": self.categories
        }



    def get_notes(self, filename):
        def get_number_ftnote(line, num_tag_list):
            num_in_text_p = re.compile("<\*\d+>(\d+)")
            num_in_tag = num_tag_list[0][1]
            num_in_text_match = num_in_text_p.match(line)
            num_in_text = num_in_text_match.group(0)
            #assert num_in_tag in num_in_text
            return num_in_tag

        def pre_parse_notes(filename):
            lines = []
            with open(filename) as f:
                for line in f:
                    line = line.replace("\n", "").replace("\r", "")
                    if line.find("b1") != line.rfind("b1"):
                        for new_line in line.split("@b1")[1:]:
                            lines.append(new_line)
                    else:
                        lines.append(line)
            return lines

        notes = []
        lines = pre_parse_notes(filename)
        for line_n, line in enumerate(lines):
            line = line.replace("\xef\xbb\xbf", "")
            num_tag_list = re.findall("(<\*(\d+)>)", line)
            assert len(num_tag_list) in [0, 1]
            if len(num_tag_list) == 0:
                notes[-1] += line
                continue
            line = self.replace_tags(line, skip_html=True, skip_ftnotes=True)
            num_in_tag = get_number_ftnote(line, num_tag_list)
            line = line.replace(num_in_tag, "", 1)
            line = "{}. {}".format(num_in_tag, line)
            notes.append(line)

        self.notes = notes


class Footnotes:
    def __init__(self, notes, parser):
        self.notes = notes
        self.parser = parser
        self.which_ch = 1 # this tells us where we are in ftnotes_by_chapter determined according to self.lines_starting_section
        self.curr_note = 0 # this tells us where we are within each chapter
        self.notes_found = 0 # this tells us how many footnotes we've seen overall

        #following two variables are supposed to be almost like mirror images
        #ftnotes_by_chapter has all of the footnotes according to footnotes file whereas text_by_chapter has all the footnotes as they are used in main text file
        self.ftnotes_by_chapter = {}
        self.text_by_chapter = {}


    def determine_start_of_note(self, line):
        note_begins_with = None
        full_match = re.findall("@n1<\*(\d+)>.*?(\d+)@n2", line)
        partial_match = re.findall("@n1(\d+)@n2", line)
        if full_match:
            full_match = full_match[0]
            note_begins_with = "<*{}>{}".format(full_match[0], full_match[1])
        elif partial_match:
            partial_match = partial_match[0]
            note_begins_with = "<*{}>".format(partial_match)
        return note_begins_with


    def reset_curr_note(curr_note, which_ch):
        # excess footnotes in footnote file than in main text file
        if curr_note == 51 and which_ch == 4:
            return (1, 5)
        #elif curr_note == 28 and which_ch == 13:
        #    return (1, 14)
        else:
            return (curr_note, which_ch)

    def no_footnote(which_ch, curr_note):
        if which_ch == 7 and curr_note == 41:
            return True
        else:
            return False

    def increment_curr_note(self):
        self.curr_note += 1
        # perform check to make sure curr_note is within bounds of ftnotes_by_chapter[which_ch]
        if self.curr_note >= len(self.ftnotes_by_chapter[self.which_ch]):
            print "Went beyond the bounds of chapter {}".format(self.which_ch)
            self.which_ch += 1

    def break_up_text(self):
        #first just move any line with footnotes from main text into variable all_lines_with_ftnotes
        self.text_by_chapter = [[]]
        all_lines_with_ftnotes = []
        for i, chapter in enumerate(self.parser.chapters_with_ftnotes):
            all_lines_with_ftnotes += [line for line in self.parser.text["en"][chapter] if "@n1" in line]

        #now the logic is basically the same as break_up_ftnotes() above, just organize into a dict when numbers re-start at a lower number indicating new chapter
        prev_num1 = 0
        for line in all_lines_with_ftnotes:
            note = self.determine_start_of_note(line)
            match = re.findall("<*(\d+)>", note)
            assert match
            num1 = match[0]
            num1 = int(num1)
            if num1 < prev_num1:
                # new chapter
                self.text_by_chapter.append([])
            self.text_by_chapter[-1].append([note, line])
            prev_num1 = num1


    def break_up_ftnotes(self):
        prev_num1 = 0
        self.ftnotes_by_chapter = [[]]
        prev_match = None
        for i, line in enumerate(self.notes):
            intentional_unmatch = line.startswith("!*?")  # I intentionally modified the file with these characters so that content workers would know where to place missing footnotes
            if intentional_unmatch:
                continue
            match = re.findall("(<\*(\d+)>(\d+))", line)
            if not match:
                self.ftnotes_by_chapter[-1][-1][1] += " "+line
                prev_match = match
                continue
            note, num1, num2 = match[0]
            num1 = int(num1)
            num2 = int(num2)
            if num1 < prev_num1:
                # new chapter
                self.ftnotes_by_chapter.append([])
            self.ftnotes_by_chapter[-1].append([note, line])
            prev_num1 = num1
            prev_match = match

    def missing_ftnotes_report(self):
        def complain_if_any_missing(missing, relevant_text, complaint):
            if missing:
                print complaint
                for ftnote_symbol in missing:
                    for ftnote in relevant_text:
                        if ftnote.startswith(ftnote_symbol):
                            print ftnote

        self.break_up_ftnotes()
        self.break_up_text()
        for ftnotes, text in zip(self.ftnotes_by_chapter, self.text_by_chapter):
            ftnotes_symbols, ftnotes_text = zip(*ftnotes)
            text_symbols, text_text = zip(*text)
            ftnotes_symbols = set(ftnotes_symbols)
            text_symbols = set(text_symbols)

            relevant_text = ftnotes_text
            complaint = "Footnotes missing in Notes.txt:"
            missing = ftnotes_symbols - text_symbols
            complain_if_any_missing(missing, relevant_text, complaint)


            relevant_text = text_text
            complaint = "Footnotes missing in main text file:"
            missing = text_symbols - ftnotes_symbols
            complain_if_any_missing(missing, relevant_text, complaint)






        #go through each chapter, zip the ftnotes and text together and figure out which ones are missing and report

        # for comment_ch_n, comments in self.text_by_chapter.items():
        #     for comment in comments:
        #         if comment in self.parser.lines_starting_sections:
        #             self.notes_found += self.curr_note
        #             self.curr_note = 0
        #         note_begins_with = self.determine_start_of_note(comment)  # which_ch 7 and curr_note 41 just continue
        #         #if no_footnote(which_ch, curr_note):
        #         #    continue
        #
        #         if ftnotes_this_ch[self.curr_note].startswith(note_begins_with):
        #             self.increment_curr_note()
        #             ftnotes_this_ch = self.ftnotes_by_chapter[self.which_ch]
        #         else:
        #             #keep track of matches so as not to get false positives
        #             note_matches = []
        #             found = False
        #             #create a range usually between 5 before and 5 after but limit it by the bounds of the array
        #             max_note = min(len(ftnotes_this_ch), self.curr_note+5)
        #             min_note = max(0, self.curr_note-5)
        #             for i in range(min_note, max_note):
        #                 if ftnotes_this_ch[i].startswith(note_begins_with):
        #                     note_matches.append(ftnotes_this_ch[i])
        #                     self.increment_curr_note()
        #                     ftnotes_this_ch = self.ftnotes_by_chapter[self.which_ch]
        #                     found = True
        #                     break
        #             if not found:
        #                 print ftnotes_this_ch[self.curr_note]
        #                 self.increment_curr_note()
        #                 ftnotes_this_ch = self.ftnotes_by_chapter[self.which_ch]



