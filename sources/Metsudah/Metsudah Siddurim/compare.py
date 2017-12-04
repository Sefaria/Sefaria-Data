#encoding=utf-8
import codecs
import csv
import os
from sources.functions import *
import re
tags_set = set()
def get_map(csv_file):
    char_map = {}
    reader = csv.reader(csv_file)
    for row in reader:
        char_map[row[0]] = row[1]
    return char_map

def get_text(files):
    files = os.listdir("Weekday Siddur Ashkenaz")
    files = ["Weekday Siddur Ashkenaz/"+f for f in files if f.endswith(".txt")]
    text = []
    for f in sorted(files, key=lambda x: int(x.replace("Weekday Siddur Ashkenaz/F", "").replace(".txt", ""))):
        with open(f) as open_file:
            file_text = list(open_file)
            for i, line in enumerate(file_text):
                line = line.replace('‘‘', '"').replace('’’', '"').replace("\r", "")
                text.append(line)
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
    return words

def replace_chars(text, char_map, heb_indices):
    bad_char_and_line = {}
    inside_tag = False
    for index in heb_indices:
        prev = text[index]
        text[index] = split_spaces_and_tags(text[index])
        text_as_str = " ".join(text[index])
        for word_n, word in enumerate(text[index]):
            if any_hebrew_in_str(word):
                for k, v in char_map.items():
                    text[index][word_n] = text[index][word_n].replace(k, v)
                poss_probs = re.findall(u"[^\u0591-\u05F4]{1}", text[index][word_n].decode('utf-8'))
                bad_chars = re.findall(u"""[^\s\[\]\)\(\,\:\;\'\.\"\'\-]""", " ".join(poss_probs))
                for bad_char in bad_chars:
                    bad_char = bad_char.encode('utf-8')
                    already_found = bad_char_and_line.get(bad_char, [])
                    if len(already_found) < 2:
                        bad_char_and_line[bad_char] = already_found + [text_as_str]

        text[index] = " ".join(text[index])
    return text, bad_char_and_line
#
# def replace_chars(text, char_map, heb_indices):
#     bad_chars = [u'ƒ', u'€', u'‰', u'‡', u'†', u'„', u'‹', u'•', u'˜', u'|']
#     bad_char_and_line = {k.encode('utf-8'): [] for k in bad_chars}
#     inside_tag = False
#     for index in heb_indices:
#         prev = text[index]
#         text[index] = text[index].split(" ")
#         text_as_str = " ".join(text[index])
#         for word_n, word in enumerate(text[index]):
#             if any_hebrew_in_str(word):
#                 for k, v in char_map.items():
#                     text[index][word_n] = text[index][word_n].replace(k, v)
#
#                 for bad_char in bad_char_and_line.keys():
#                     if bad_char in text[index][word_n] and len(bad_char_and_line[bad_char]) < 2:
#                         bad_char_and_line[bad_char].append(text_as_str)
#
#         text[index] = " ".join(text[index])
#     return text, bad_char_and_line

def remove_tags(line):
    for tag in re.findall("<.*?>", line):
        line = line.replace(tag, "")
    return line

def get_heb_indices(text):
    indices = []
    for i, line in enumerate(text):
        len_line = len(line)
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
    pass

if __name__ == "__main__":
    with open('metsudah code.csv') as f:
        char_map = get_map(f)
    text = get_text("Weekday Siddur Ashkenaz")
    heb_subset = get_heb_indices(text)
    text, bad_char_and_line = replace_chars(text, char_map, heb_subset)
    correct_hebrew_in_tags(text, char_map)
    for letter, probs in bad_char_and_line.iteritems():
        for prob in probs:
            print "{} => {}".format(letter, prob)


