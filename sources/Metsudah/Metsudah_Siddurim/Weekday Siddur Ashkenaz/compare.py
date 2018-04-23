#encoding=utf-8
import codecs
import csv
import os
from sources.Metsudah.Metsudah_Siddurim.metsudah_parser import Metsudah_Parser

from sources.functions import *
import re
tags_set = set()


def get_map(csv_file):
    char_map = {}
    reader = csv.reader(csv_file)
    for row in reader:
        char_map[row[0]] = row[1]
    return char_map

def get_text(file):
    # files = os.listdir("Weekday Siddur Ashkenaz")
    # files = ["Weekday Siddur Ashkenaz/"+f for f in files if f.endswith(".txt")]
    # text = []
    # for f in sorted(files, key=lambda x: int(x.replace("Weekday Siddur Ashkenaz/F", "").replace(".txt", ""))):
    #     with open(f) as open_file:
    #         file_text = list(open_file)
    #         paragraph_end = '¶'
    #         temp_line = ""
    #         for i, line in enumerate(file_text):
    #             line = line.replace('‘‘', '"').replace('’’', '"').replace("\r", "").replace("\n", "")
    #             temp_line += line
    #             if paragraph_end in line:
    #                 temp_line = temp_line.replace(paragraph_end, "")
    #                 text.append(temp_line)
    #                 temp_line = ""
    onefile = open(file)
    text = list(onefile)
    return text

def split_spaces_and_tags(line):
    #when inside tag, keep adding char to a word,
    #when exiting tag, add tag, when encountering space and not inside tag, add word
    inside_tag = False
    words = []
    curr_word = ""
    for char_n, char in enumerate(line):
        if char == "<":
            inside_tag = True
            if curr_word != "":
                words.append(curr_word)
                curr_word = ""
            curr_word += char
        elif char == ">":
            inside_tag = False
            curr_word += char
            tags_set.add(curr_word)
            tags_set.add(curr_word)
            words.append(curr_word)
            curr_word = ""
        elif inside_tag:
            curr_word += char
        elif not inside_tag:
            if char == " ":
                words.append(curr_word)
                curr_word = ""
            else:
                curr_word += char
    if curr_word != "":
        words.append(curr_word)
    return [word for word in words if word]

def replace_chars(text, char_map, heb_indices):
    bad_char_and_line = {}
    inside_tag = False
    cantillation_indices = {}
    for index in heb_indices:
        prev = text[index]
        text[index] = split_spaces_and_tags(text[index])
        text_as_str = " ".join(text[index])
        for word_n, word in enumerate(text[index]):
            is_tag = word[0] == "<" and word[-1] == ">"
            if is_tag:
                continue
            has_hebrew = any_hebrew_in_str(word)
            exceptions = ["lB", "aB", "aB:"] #seemingly English words that are really Hebrew that simply need to be converted
            if has_hebrew or word in exceptions:
                for k, v in char_map.items():
                    if k in text_as_str and re.findall("[a-zA-Z]{1}", k) == []:
                        if k not in cantillation_indices:
                            cantillation_indices[k] = set()
                        cantillation_indices[k].add(index)
                    text[index][word_n] = text[index][word_n].replace(k, v)
                poss_probs = re.findall(u"[^\u0591-\u05F4]{1}", text[index][word_n].decode('utf-8'))
                bad_chars = re.findall(u"""[^\s\[\]\)\(\,\:\;\'\.\"\'\-]""", " ".join(poss_probs))
                for bad_char in bad_chars:
                    bad_char = bad_char.encode('utf-8')
                    already_found = bad_char_and_line.get(bad_char, [])
                    if len(already_found) < 2:
                        bad_char_and_line[bad_char] = already_found + [text_as_str]

        text[index] = " ".join(text[index])
    return text, bad_char_and_line, cantillation_indices


def remove_tags(line):
    for tag in re.findall("<.*?>", line):
        line = line.replace(tag, "")
    return line

def get_heb_indices(text):
    indices = []
    for i, line in enumerate(text):
        any_hebrew = any_hebrew_in_str(line)
        if any_hebrew:
            indices.append(i)
    return indices


def get_ords_line(line):
    ords = []
    spaces = 0
    for i in range(len(line) / 2):
        start = i*2 - spaces
        end = i*2 + 2 - spaces
        if line[start] == " ":
            ords.append(u" ")
            spaces += 1
        else:
            char_to_add = line[start:end].decode('utf-8')
            ords.append(char_to_add)
    return ords

def can_decode(line):
    try:
        line.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False

def create_txts_for_diff():
    dgs = open("dgs.txt").read()
    norm = open("norm.txt").read()
    dgs_char_per_line = codecs.open("dgs_char_per_line.txt", 'w', encoding='utf-8')
    norm_char_per_line = codecs.open("norm_char_per_line.txt", 'w', encoding='utf-8')
    for char in get_ords_line(norm):
        norm_char_per_line.write(char+u"\n")
    for char in get_ords_line(dgs):
        dgs_char_per_line.write(char+u"\n")

def correct_hebrew_in_tags(text, char_map):
    # replaced english characters inside tags accidentally and need to revert them to their previous values
    inverted_char_map = {v: k for k, v in char_map.iteritems()}
    inside_tag = False
    for line_n, line in enumerate(text):
        for char_n, char in enumerate(line):
            if char == "<":
                inside_tag = True
            elif char == ">":
                inside_tag = False
            elif inside_tag:
                replace_char = inverted_char_map.get(line[char_n: char_n+2], None)
                if replace_char:
                    text[line_n][char_n] = replace_char
    return text

def sort_indexes(cantillation_indices):
    for mark, indices in cantillation_indices.iteritems():
        cantillation_indices[mark] = sorted(list(indices))
    return cantillation_indices

def get_all_tags(text):
    tags_set = set()
    for line in text:
        tags_in_line = re.findall("<.*?>", line)
        for tag in tags_in_line:
            tags_set.add(tag)
    return tags_set


if __name__ == "__main__":
    with open('metsudah code.csv') as f:
         char_map = get_map(f)
    orig_text = get_text("weekday_tagged_updated.txt")
    heb_subset = get_heb_indices(orig_text)
    decoded_text, bad_char_and_line, cantillation_indices = replace_chars(orig_text, char_map, heb_subset)
    with open("./weekday_tagged_updated_converted.txt", 'w') as f:
        for line in decoded_text:
            f.write(line)
    cantillation_indices = sort_indexes(cantillation_indices) #places where cantillation marks appear
    text = correct_hebrew_in_tags(decoded_text, char_map)
    cats = ["Liturgy"]
    parser = Metsudah_Parser("Siddur Sefard Linear", u"סידור ספרד דו לשוני", cats=cats, vtitle="The Metsudah Siddur...",
                vsource="http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002211687", input_text=text, node_separator="|")
    parser.parse_into_en_and_he_lists()
    parser.replace_tags_in_all_lines()
    parser.create_schema()
    post_index(parser.index, server="http://localhost:8000")
    #parser.post_text("http://draft.sefaria.org")
