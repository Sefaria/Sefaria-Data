#encoding=utf-8
from sources.functions import *

class Metsudah_Parser:
    def __init__(self, en_title, he_title, input_text=[]):
        self.en_title = en_title
        self.he_title = he_title
        self.input_text = input_text
        self.current_he_ja_node = ""
        self.current_en_ja_node = ""
        self.ja_nodes = []
        self.root_node = SchemaNode()
        self.prev_line_instruction = False
        self.text = {"en": {}, "he": {}} #"en" -> english nodes -> list of english comments; "he" -> english_nodes -> list of hebrew comments
        self.en_to_he = {} #which english corresponds to which hebrew node
        self.en_ja_times = 0
        self.he_ja_times = 0

    def is_instruction(self, line):
        instruction_tags = ["<M in>", "<M ex>", "<M t2>", "<M t1>"]
        instruction = any([tag in line for tag in instruction_tags])
        instruction = instruction or (self.prev_line_instruction and line.startswith("<EM>"))
        return instruction

    def replace_tags(self, line, remove_all=True):
        tags_in_line = re.findall("<.*?>", line)
        for tag in tags_in_line:
            remove = remove_all or not tag in ["<i>", "<b>", "</i>", "</b>", "<br>"]
            if remove:
                line = line.replace(tag, "")
        return line

    def is_header(self, line):
        headers = ["<M ct>", "<M kot>"]
        for h in headers:
            if h in line:
                return True
        return False


    def try_to_set_current_ja(self, line):
        if self.is_header(line):
            line = self.replace_tags(line, remove_all=True).strip()
            if any_english_in_str(line):
                self.en_ja_times += 1
                self.current_en_ja_node = line
                if self.current_en_ja_node in self.text['en'].keys():
                    self.current_en_ja_node += "2"
                self.text["en"][self.current_en_ja_node] = []
                self.prev_line_en_title = self.current_en_ja_node
            elif any_hebrew_in_str(line):
                self.he_ja_times += 1
                self.text["he"][self.current_en_ja_node] = []
                self.current_he_ja_node = line.decode('utf-8')
                assert self.prev_line_en_title
                self.en_to_he[self.prev_line_en_title] = self.current_he_ja_node
                self.prev_line_en_title = None


    def parse_into_en_and_he_lists(self):
        self.prev_line_instruction = False
        for line_n, line in enumerate(self.input_text):
            orig_line = line
            line = line.replace("’", "'").replace('﻿', "")
            self.try_to_set_current_ja(line)
            if not self.current_en_ja_node:
                continue
            instruction = self.is_instruction(line)
            temp_line = self.replace_tags(line, remove_all=True)  # temp_line needs to be tagless
            line = self.replace_tags(line, remove_all=False)  # but in line dont remove all tags, just some
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

    def add_line(self, line, lang):
        self.text[lang][self.current_en_ja_node].append(line)


    def create_schema(self):
        root = SchemaNode()
        root.add_primary_titles()
        for en, he in self.en_to_he.items():
            node = JaggedArrayNode()
            node.add_primary_titles(en, he)
            node.add_structure(["Paragraph"])