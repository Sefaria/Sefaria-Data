# -*- coding: utf-8 -*-

import re
from sefaria.model import *
from sources.functions import *
from sefaria.system.exceptions import *


def parse(lines):
    prev_ch = 1
    prev_v = 1
    text = {}
    for count, line in enumerate(lines):
        orig_line = line
        ch_v_finds = re.findall(u"@\d+\[.*?,.*?\]@?\d?", line)
        assert len(ch_v_finds) in [0, 1]
        if len(ch_v_finds) is 0:
            sham = re.findall(u"@\d+\[שם.*?\]", line)
            if len(sham) is 1:
                line = line.replace(sham[0], "")
        elif len(ch_v_finds) is 1:
            line = line.replace(ch_v_finds[0], "")
            ch, v = parse_ch_v(ch_v_finds[0])
            if ch not in text:
                text[ch] = {}
            if v not in text[ch]:
                text[ch][v] = []
        if len(line) > 0:
            text[ch][v].append(line)
    return text

def parse_ch_v(ch_v):
    ch_v = ch_v.replace(", ", ",")
    ch_v_first_at = ch_v.find("@")
    ch_v_last_at = ch_v.rfind("@")
    if ch_v_last_at > ch_v_first_at:
        ch_v = ch_v[ch_v_first_at:ch_v_last_at]
    else:
        ch_v = ch_v[ch_v_first_at:]
    ch_v = ch_v.split("-")[0]  # if there is a range, take the beginning of the range
    ch, v = ch_v.split(",")[0], ch_v.split(",")[1]
    ch = getGematria(ch)
    v = getGematria(v)
    return ch, v

def get_en_book(he_book):
    try:
        title = library.get_index(he_book).title
    except BookNameError:
        title_wout_first_word = " ".join(he_book.split(" ")[1:])
        title = library.get_index(title_wout_first_word).title
    return title


def pre_parse(file):
    '''
    to deal with: torah special case, file 3 with its broken up brackets and lines, file 2 without verses
    '''
    text = {}
    lines = []
    for line in file:
        orig_line = line
        line = line.replace("\n", "").decode('utf-8')
        is_header = line.split(" ")
        start_book_of_torah = line.startswith("@2") and u"פרשת" not in line and not line.startswith("@22")
        start_book_of_nach = line.startswith("@22") or line.startswith("@00")
        if start_book_of_torah and "[" not in line and "]" not in line:
            line = line.replace("@2", "")
            if len(lines) > 0:
                text[(en_book, he_book)] = parse(lines)
                lines = []
            en_book = "Torah, {}".format(get_en_book(line))
            he_book = line
            text[(en_book, he_book)] = parse(lines)
            lines = []
        elif start_book_of_nach and "[" not in line and "]" not in line:
            line = line.replace("@22", "").replace("@00", "")
            if len(lines) > 0:
                text[(en_book, he_book)] = parse(lines)
                lines = []
            en_book = get_en_book(line)
            he_book = line
            text[(en_book, he_book)] = {}

        elif u"פרשת" not in line:
            ch_v_marker = re.findall(u"@\d+\[.*?\]@\d+", line)
            lines.append(line)

    if len(lines) > 0:
        text[(en_book, he_book)] = parse(lines)
    return text


def create_schema(en, he):
    root = JaggedArrayNode()
    comm_en = "Chomat Anakh on {}".format(en)
    comm_he = u"חומת אנך על ".format(he)
    root.add_primary_titles(comm_en, comm_he)
    root.add_structure(["Chapter", "Verse", "Paragraph"])
    root.validate()
    index = {
        "dependence": "Commentary",
        "base_text_titles": [en],
        "base_text_mapping": "many_to_one",
        "title": en,
        "schema": root.serialize(),
        "categories": ["Tanakh", "Commentary", "Chomat Anakh", ]
    }
    post_index(index)

def post_books(text_dict):
    for en, he in text_dict.keys():
        create_schema(en, he)



if __name__ == "__main__":
    text1 = pre_parse(open("chomat anakh1.txt"))
    text3 = pre_parse(open("chomat anakh3.txt"))
    post_books(text1)
    pass