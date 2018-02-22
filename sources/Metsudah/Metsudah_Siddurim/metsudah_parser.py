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
        self.ftnote_tags = ["@n1", "@n2", "@b1", "@b2"]
        self.html_tags = ["<i>", "<b>", "</i>", "</b>", "<br>", "<small>", "</small>", "<sup>", "</sup>"]
        self.language_tags = ["<ENG>", "<EN>", "<HE>", "<HEB>", "<heb>", "<eng>", "<en>", "<he>", "<heb>"]
        self.chapters = []



    def pre_parse(self):
        orig_text = list(open(self.input_text))
        bad_chars = Counter()
        replacements = [("׀", "—"), ("_", "-"), ("±", "-"), ("<TIE>", " "), ("<IT>", "<i>"), ("<HEB>קּ<SZ14>", "❖"),
                        ("<ITC>", "</i>"), ("@ss", "<small>"), ("@sr", "</small>"), ("@eb", "<b>"), ("@hb", "<b>"),
                        ("@hi", "<small>"), ("@vs", "<small>"), ("@y1", "<small>"), ("@ei", "<small>")]
        he_replacements = [("r", "ע"), ("H", "לֹּ"), ("G", "לֹ"), ("x", "רֹּ"), ("§", "ךָ"), ("-", "־")]
        it_only = []
        itc_only = []
        for line_n, line in enumerate(orig_text):
            orig_text[line_n] = orig_text[line_n].replace("\r\n", "")

            #first make replacements and then remove non-html and non-ftnote related tags
            if "@vs" in line:
                pos = line.find("@vs")
                next_tag_pos = line[pos+3:].find("@") + pos + 3
                next_tag = line[next_tag_pos:next_tag_pos+3]
                line = line[0:pos] + line[pos:].replace(next_tag, "</small>", 1)
                orig_text[line_n] = line
            for replacement in replacements:
                orig_text[line_n] = orig_text[line_n].replace(replacement[0], replacement[1])
            orig_text[line_n] = self.replace_tags(orig_text[line_n], skip_html=True, skip_ftnotes=True, skip_header=True, skip_language=True)

            #now remove extra <i>s and replace replacements
            if "<i>" in orig_text[line_n] and not "</i>" in orig_text[line_n]:
                orig_text[line_n] = orig_text[line_n].replace("<i>", "")
            elif "</i>" in orig_text[line_n] and not "<i>" in orig_text[line_n]:
                orig_text[line_n] = orig_text[line_n].replace("</i>", "")
            if "<b>" in orig_text[line_n] and not "</b>" in orig_text[line_n]:
                orig_text[line_n] = orig_text[line_n] + "</b>"

            if "<small>" in orig_text[line_n] and not "</small>" in orig_text[line_n]:
                orig_text[line_n] = orig_text[line_n] + "</small>"

            orig_text[line_n] = orig_text[line_n].replace("<b><b>", "<b>").replace("<i><i>", "<i>").replace("<small><small>", "<small>")




            #for hebrew text, do he_replacements only in hebrew lines and in hebrew lines, only in hebrew words
            if not any_hebrew_in_str(orig_text[line_n]):
                continue
            orig_text[line_n] = orig_text[line_n].replace(">", "> ") #this is just so that tags will become their own words
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
            if self.current_en_ja_node not in self.chapters:
                self.chapters.append(self.current_en_ja_node)
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
                line = self.replace_tags(line)
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
        ftnote_pattern = "<\*\d+>"
        headers = self.instruction_tags + self.headers

        tags_in_line = re.findall("<.*?>|@[a-zA-Z0-9]{1,2}", line)
        for tag in tags_in_line:
            remove = True
            if skip_ftnotes and (tag in self.ftnote_tags or re.findall(ftnote_pattern, tag)):
                remove = False
            if skip_html and (tag in self.html_tags or re.findall("<i class='footnote'>", tag)):
                remove = False
            if skip_header and tag in headers:
                remove = False
            if skip_language and tag in self.language_tags:
                remove = False
            if remove:
                line = line.replace(tag, "")

        # forbidden_in_node_titles = ["."]
        # for char in forbidden_in_node_titles:
        #     line = line.replace(char, "")
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
                result = post_text(ref, send_text, server=server)
                if "error" in result:
                    if text != []:
                        print "Problem with {}".format(ref)


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
        self.complaints = {"notes": [], "main": [], "duplicates": []}
        self.map_sefaria_chapters_to_ftnote_chapters = {} #by ftnote chapters, I mean 1...n groups of footnotes that do not neatly
                                                          #correspond to nodes being used in Index
        self.all_lines = [] #all lines in main text

        '''
        both break_up_text and break_up_footnotes do about the same thing, both dividing up either footnotes or text into corresponding
        equal number of sections
        '''
        self.break_up_ftnotes()
        self.break_up_text()


    def break_up_text(self):
        #the logic is basically the same as break_up_ftnotes() above,
        #just organize into a dict when numbers re-start at a lower number indicating new chapter
        #main difference is that there can be more than one footnote per line
        self.text_by_chapter = [{}]
        prev_num1 = 0
        for i, chapter in enumerate(self.parser.chapters):
            for line_n, line in enumerate(self.parser.text["en"][chapter]):
                if "@n1" not in line:
                    continue
                line = self.parser.replace_tags(line, skip_header=True, skip_ftnotes=True)
                notes = re.findall("@n1(.*?)@n2", line)
                for note in notes:
                    note = note.strip()
                    if note.isdigit():
                        num1 = int(note)
                        note = "<*{}>{}".format(note, note)
                    else:
                        match = re.findall("<*(\d+)>", note)
                        num1 = int(match[0])
                    if num1 <= prev_num1:
                        # new chapter
                        self.text_by_chapter.append({})
                    if note in self.text_by_chapter[-1]:
                        duplicate = self.text_by_chapter[-1][note]
                        self.complaints["duplicates"].append(line)
                        self.complaints["duplicates"].append(duplicate)
                    self.text_by_chapter[-1][note] = line
                    if chapter not in self.map_sefaria_chapters_to_ftnote_chapters:
                        self.map_sefaria_chapters_to_ftnote_chapters[chapter] = {}
                    self.map_sefaria_chapters_to_ftnote_chapters[chapter][line_n] = (len(self.text_by_chapter)-1, note)
                    prev_num1 = num1


    def break_up_ftnotes(self):
        prev_num1 = 0
        self.ftnotes_by_chapter = [{}]
        prev_match = None
        for i, line in enumerate(self.notes):
            line = self.parser.replace_tags(line, skip_header=True, skip_ftnotes=True)  #just need to remove language markers here
            note = re.findall("@b1(.*?)@b2", line)
            if not note or note[0] == "":
                self.ftnotes_by_chapter[-1][prev_note] += " "+line
                continue

            full_note = re.findall("<\*(\d+)>\s?(\d+)", line)
            if full_note:
                num1, num2 = full_note[0]
                num1 = int(num1)
                note = "<*{}>{}".format(num1, num2)
            else:
                num1 = int(note)
                note = "<*{}>{}".format(note, note)

            if num1 <= prev_num1:
                self.ftnotes_by_chapter.append({})    # new chapter
            for tag in self.parser.ftnote_tags:
                line = line.replace(tag, "")

            if note in self.ftnotes_by_chapter[-1]:
                #flag it
                duplicate = self.ftnotes_by_chapter[-1][note]
                self.complaints["duplicates"].append(line)
                self.complaints["duplicates"].append(duplicate)

            self.ftnotes_by_chapter[-1][note] = line
            prev_num1 = num1
            prev_note = note


    def add_complaint_if_any_missing(self, missing, relevant_text, complaint):
        if missing:
            for ftnote_symbol in missing:
                for ftnote in relevant_text:
                    if ftnote_symbol in ftnote:
                        self.complaints[complaint].append(ftnote)

    def missing_ftnotes_report(self):
        #checks both ftnotes and main text to see if either ftnotes are missing in main text or ftnotes file
        chapter = 0
        for ftnotes, text in zip(self.ftnotes_by_chapter, self.text_by_chapter):
            chapter += 1
            ftnotes_symbols, ftnotes_arr = ftnotes.keys(), ftnotes.values()
            text_symbols, text_arr = text.keys(), text.values()
            ftnotes_symbols = set(ftnotes_symbols)
            text_symbols = set(text_symbols)

            relevant_text = ftnotes_arr
            complaint = "notes"
            missing = ftnotes_symbols - text_symbols
            self.add_complaint_if_any_missing(missing, relevant_text, complaint)

            relevant_text = text_arr
            complaint = "main"
            missing = text_symbols - ftnotes_symbols
            self.add_complaint_if_any_missing(missing, relevant_text, complaint)


    def insert_ftnotes_into_text(self):
        #text_by_chapter contains text roughly as it appears in main text file,
        #now each key (<*1>1) will point to the line with ftnote replaced by text from Notes.txt if there are no self.complaints
        for key in self.complaints:
            if self.complaints[key]:
                return

        for i, chapter in enumerate(self.parser.chapters):
            for line_n, line in enumerate(self.parser.text["en"][chapter]):
                if "@n1" in line:
                    line = self.parser.replace_tags(line, skip_ftnotes=True, skip_header=True)
                    ch_num, ftnote_symbol = self.map_sefaria_chapters_to_ftnote_chapters[chapter][line_n]
                    curr_str = self.text_by_chapter[ch_num][ftnote_symbol]
                    ftnotes = self.ftnotes_by_chapter[ch_num]
                    if ftnote_symbol not in ftnotes.keys():
                        print "PROBLEM with {}".format(line)
                    else:
                        sup_num = re.findall("<\*(\d+)>", ftnote_symbol)[0]
                        insert_text = "<sup>{}</sup><i class='footnote'>{}</i>".format(sup_num, ftnotes[ftnote_symbol].replace(ftnote_symbol, ""))
                        symbol_re = re.findall("@n1.{{0,2}}{}.{{0,2}}@n2".format(ftnote_symbol), curr_str)[0]
                        start_ftnote = curr_str.find(symbol_re)
                        end_ftnote = curr_str.find(symbol_re) + len(symbol_re)
                        assert end_ftnote > start_ftnote >= 0  # assert we found it
                        curr_str = curr_str[0:start_ftnote] + insert_text + curr_str[end_ftnote:]
                        line = curr_str
                self.parser.text["en"][chapter][line_n] = self.parser.replace_tags(line, skip_html=True)



